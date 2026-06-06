import os
import sys
import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv(override=True)


key = os.getenv("OPENAI_API_KEY")
if key:
    print(f"Loaded key: starts {key[:8]}... ends ...{key[-4:]}  (length {len(key)})")
else:
    print("No OPENAI_API_KEY found in environment!")


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def create_daily_thought() -> str:
    """Generate an inspirational daily thought using the LLM."""
    llm = ChatOpenAI(model="gpt-4o-mini")
    response = llm.invoke("Generate a short, unique inspirational daily thought in one or two sentences.")
    return response.content

def get_post(post_id: int) -> str:
    """Fetch a post by ID from JSONPlaceholder."""

    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        post = response.json()

        result = (
            f"Post ID: {post['id']}\n"
            f"User ID: {post['userId']}\n"
            f"Title: {post['title']}\n"
            f"Body: {post['body']}"
        )

        print(result)
        return result

    except Exception as e:
        error_msg = f"Error fetching post: {str(e)}"
        print(error_msg)
        return error_msg
    


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_recent_email_subjects() -> str:
    """Fetch subjects of the 2 most recent Gmail emails."""

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me",
        maxResults=2
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        return "No emails found."
    
    output = ["Your 2 Most Recent Emails:\n"]

    for index, msg in enumerate(messages, start=1):
        email = service.users().messages().get(
            userId="me",
            id=msg["id"]
        ).execute()

        headers = email["payload"]["headers"]

        subject = next(
            (h["value"] for h in headers if h["name"] == "Subject"),
            "No Subject"
        )

        output.append(f"{index}. Subject: {subject}")

    return "\n".join(output)

agent = create_agent(
    model="openai:gpt-4o",    
    tools=[get_weather, create_daily_thought, get_post, get_recent_email_subjects],
    system_prompt="You are a helpful assistant. Make sure that you only respond with whatever is coming as input to the agent, and do not add any extra commentary or explanation.",
)

if len(sys.argv) < 2:
    print("Usage: python dynamic_agent_input.py \"<your message>\"")
    sys.exit(1)

user_input = " ".join(sys.argv[1:])

result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
print(result["messages"][-1].content)
