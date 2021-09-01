import os
from pathlib import Path
import dataclasses
import pickle

from pyairtable import Table

from slack_sdk import WebClient
from slack_sdk.web import SlackResponse

from slack_bolt import App, Ack
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.workflows.step import Configure, Update, Complete, Fail, WorkflowStep


@dataclasses.dataclass
class StudentData:
    first_name: str
    last_name: str
    email: str
    project_title: str
    channel_name: str
    subject1: str
    subject2: str
    thesis_type: str
    start_date: str
    end_date: str
    primary_supervisor: str
    secondary_supervisor: str

def add_student_record(studentData : StudentData):
    table = Table(os.environ["AIRTABLE_API_KEY"], 'appJu48k8OobcBngX', 'Theses')
    table.create({'First Name': studentData.first_name,
                    'Last Name': studentData.last_name,
                    'Email': studentData.email,
                    'Project title': studentData.project_title,
                    'Channel Name': studentData.channel_name,
                    'Subject 1': studentData.subject1,
                    'Subject 2': studentData.subject2,
                    'Thesis type': studentData.thesis_type,
                    'Start date': studentData.start_date,
                    'End date': studentData.end_date,
                    'Primary supervisor': studentData.primary_supervisor,
                    'Secondary supervisor': studentData.secondary_supervisor
    })

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
)


    try:
        # Call views.publish with the built-in client
        client.views_publish(
            # Use the user ID associated with the event
            user_id=event["user"],
            # Home tabs must be enabled in your app configuration
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Welcome home, <@" + event["user"] + "> :house:*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                          "type": "mrkdwn",
                          "text": "Learn how home tabs can be more useful and interactive <https://api.slack.com/surfaces/tabs/using|*in the documentation*>."
                        }
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")



###### Modal example ###########

### Start modal
# Listen for a shortcut invocation
@app.shortcut("shortcut_add_new_student")
def open_modal(ack, body, client):
    # Acknowledge the command request
    ack()
    with open('new_student_modal.json') as f:
        new_student_modal_json = f.read()
    # Call views_open with the built-in client
    client.views_open(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view=new_student_modal_json
    )


#### #################
# Handle a view_submission request
@app.view("view_new_student")
def handle_submission(ack, body, client: WebClient, view, logger):
    ack()
    # Assume there's an input block with `input_c` as the block_id and `dreamy_input`
    values = view["state"]["values"]
    with open('temp','wb') as f:
        pickle.dump(values,f)
    user = body["user"]["id"]
    userdata = client.users_info(user=user)

    # Validate the inputs
    # errors = {}
    # if hopes_and_dreams is not None and len(hopes_and_dreams) <= 5:
    #     errors["input_c"] = "The value must be longer than 5 characters"
    # if len(errors) > 0:
    #     ack(response_action="errors", errors=errors)
    #     return
    # Acknowledge the view_submission request and close the modal
    studentData = StudentData
    studentData.first_name = values['first_name']['action']['value']
    studentData.last_name = values['last_name']['action']['value']
    studentData.email = values['email']['action']['value']
    studentData.project_title = values['project_title']['action']['value']
    studentData.channel_name = values['channel_name']['action']['value']
    studentData.subject1 = values['subject1']['action']['value']
    studentData.subject2 = values['subject2']['action']['value']
    studentData.thesis_type = values['thesis_type']['action']['selected_option']['value']
    studentData.start_date = values['start_date']['action']['selected_date']
    studentData.end_date = values['end_date']['action']['selected_date']
    studentData.primary_supervisor = userdata['user']['profile']['real_name_normalized']
    studentData.secondary_supervisor = values['secondary_supervisor']['action']['value']
    
    add_student_record(studentData)
    # Do whatever you want with the input data - here we're saving it to a DB
    # then sending the user a verification of their submission
    #print(client.users_identity())

    # Message to send user
    msg = ""
    try:
        # Save to DB
        msg = f"{[getattr(studentData,field.name) for field in dataclasses.fields(StudentData)]}"
    except Exception as e:
        # Handle error
        msg = "There was an error with your submission"

    # Message the user
    try:
        client.chat_postMessage(channel=user, text=msg)
    except e:
        logger.exception(f"Failed to post a message {e}")




#### Update modal
# Listen for a button invocation with action_id `button_abc` (assume it's inside of a modal)
@app.action("button_abc")
def update_modal(ack, body, client):
    # Acknowledge the button request
    ack()
    # Call views_update with the built-in client
    client.views_update(
        # Pass the view_id
        view_id=body["view"]["id"],
        # String that represents view state to protect against race conditions
        hash=body["view"]["hash"],
        # View payload with updated blocks
        view={
            "type": "modal",
            # View identifier
            "callback_id": "view_1",
            "title": {"type": "plain_text", "text": "Updated modal"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "plain_text", "text": "You updated the modal!"}
                },
                {
                    "type": "image",
                    "image_url": "https://media.giphy.com/media/SVZGEcYt7brkFUyU90/giphy.gif",
                    "alt_text": "Yay! The modal was updated"
                }
            ]
        }
    )


###### Workflow step ###############
@app.action({"type": "workflow_step_edit", "callback_id": "test_id"})
def edit(body: dict, ack: Ack, client: WebClient):
    ack()
    new_modal: SlackResponse = client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "workflow_step",
            "callback_id": "copy_review_view",
            "blocks": [
                {
                    "type": "section",
                    "block_id": "intro-section",
                    "text": {
                        "type": "plain_text",
                        "text": "Create a task in one of the listed projects. The link to the task and other details will be available as variable data in later steps.",
                    },
                },
                {
                    "type": "input",
                    "block_id": "task_name_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "task_name",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Write a task name",
                        },
                    },
                    "label": {"type": "plain_text", "text": "Task name"},
                },
                {
                    "type": "input",
                    "block_id": "task_description_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "task_description",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Write a description for your task",
                        },
                    },
                    "label": {"type": "plain_text", "text": "Task description"},
                },
                {
                    "type": "input",
                    "block_id": "task_author_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "task_author",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Write a task name",
                        },
                    },
                    "label": {"type": "plain_text", "text": "Task author"},
                },
            ],
        },
    )


@app.view("copy_review_view")
def save(ack: Ack, client: WebClient, body: dict):
    state_values = body["view"]["state"]["values"]
    response: SlackResponse = client.api_call(
        api_method="workflows.updateStep",
        json={
            "workflow_step_edit_id": body["workflow_step"]["workflow_step_edit_id"],
            "inputs": {
                "taskName": {
                    "value": state_values["task_name_input"]["task_name"]["value"],
                },
                "taskDescription": {
                    "value": state_values["task_description_input"]["task_description"][
                        "value"
                    ],
                },
                "taskAuthorEmail": {
                    "value": state_values["task_author_input"]["task_author"]["value"],
                },
            },
            "outputs": [
                {
                    "name": "taskName",
                    "type": "text",
                    "label": "Task Name",
                },
                {
                    "name": "taskDescription",
                    "type": "text",
                    "label": "Task Description",
                },
                {
                    "name": "taskAuthorEmail",
                    "type": "text",
                    "label": "Task Author Email",
                },
            ],
        },
    )
    ack()


pseudo_database = {}


@app.event("workflow_step_execute")
def execute(body: dict, client: WebClient):
    step = body["event"]["workflow_step"]
    completion: SlackResponse = client.api_call(
        api_method="workflows.stepCompleted",
        json={
            "workflow_step_execute_id": step["workflow_step_execute_id"],
            "outputs": {
                "taskName": step["inputs"]["taskName"]["value"],
                "taskDescription": step["inputs"]["taskDescription"]["value"],
                "taskAuthorEmail": step["inputs"]["taskAuthorEmail"]["value"],
            },
        },
    )
    user: SlackResponse = client.users_lookupByEmail(
        email=step["inputs"]["taskAuthorEmail"]["value"]
    )
    user_id = user["user"]["id"]
    new_task = {
        "task_name": step["inputs"]["taskName"]["value"],
        "task_description": step["inputs"]["taskDescription"]["value"],
    }
    tasks = pseudo_database.get(user_id, [])
    tasks.append(new_task)
    pseudo_database[user_id] = tasks

    blocks = []
    for task in tasks:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "plain_text", "text": task["task_name"]},
            }
        )
        blocks.append({"type": "divider"})

    home_tab_update: SlackResponse = client.views_publish(
        user_id=user_id,
        view={
            "type": "home",
            "title": {"type": "plain_text", "text": "Your tasks!"},
            "blocks": blocks,
        },
    )



# Start your app
if __name__ == "__main__":
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

