from openai import OpenAI
import os
import sys 
import json 
import shutil

openai_api_key = "EMPTY" # This can be left alone

# Uncomment depending on where you're running this script:
# openai_api_base = "http://localhost:8000/v1" # I'm running from my local machine with SSH tunneling
openai_api_base = "http://eidf219-network-machine.vms.os.eidf.epcc.ed.ac.uk:8000/v1" # I'm running from my team's VM

SYSTEM_PROMPT = """
You are Samantha, an intelligent OS assistant that lives in a command-line terminal.
Your goal is to understand a user's natural language request and translate it into a specific command formatted as a JSON object.
You must ONLY respond with the JSON object. Do not add any explanatory text, markdown formatting, or anything else outside of the JSON structure.

The user is in a Linux-like environment (openEuler).

Here are the actions you can perform:

1.  **list_files**: Show files and directories in a given path.
    - User: "Show me what's in here" -> {"action": "list_files", "parameters": {"path": "."}}
    - User: "list the files in my documents folder" -> {"action": "list_files", "parameters": {"path": "documents"}}

2.  **change_directory**: Navigate to a different folder.
    - User: "go to my project folder" -> {"action": "change_directory", "parameters": {"path": "project"}}
    - User: "cd .." -> {"action": "change_directory", "parameters": {"path": ".."}}

3.  **create_file**: Create a new, empty file.
    - User: "make a file called notes.txt" -> {"action": "create_file", "parameters": {"filename": "notes.txt"}}
    - User: "touch new_script.py" -> {"action": "create_file", "parameters": {"filename": "new_script.py"}}

4.  **create_directory**: Create a new folder.
    - User: "create a folder for my hackathon project" -> {"action": "create_directory", "parameters": {"directory_name": "hackathon_project"}}
    - User: "mkdir new_stuff" -> {"action": "create_directory", "parameters": {"directory_name": "new_stuff"}}

5.  **copy**: Copy a file or directory.
    - User: "copy file1.txt to file2.txt" -> {"action": "copy", "parameters": {"source": "file1.txt", "destination": "file2.txt"}}
    - User: "duplicate the 'images' folder and call it 'images_backup'" -> {"action": "copy", "parameters": {"source": "images", "destination": "images_backup"}}

6.  **move**: Move a file or directory.
    - User: "move report.docx into the 'archive' folder" -> {"action": "move", "parameters": {"source": "report.docx", "destination": "archive"}}

7.  **rename**: Rename a file or directory.
    - User: "rename old_name.txt to new_name.txt" -> {"action": "rename", "parameters": {"source": "old_name.txt", "destination": "new_name.txt"}}

8.  **delete**: Remove a file or directory. This is a destructive operation.
    - User: "delete temp.log" -> {"action": "delete", "parameters": {"path": "temp.log"}}
    - User: "remove the old_backups folder" -> {"action": "delete", "parameters": {"path": "old_backups"}}

9.  **find**: Search for a file or directory by its exact name.
    - User: "find a file named 'config.json'" -> {"action": "find", "parameters": {"name": "config.json"}}
    - User: "can you find the 'assets' folder?" -> {"action": "find", "parameters": {"name": "assets"}}

10. **exit**: To quit the assistant.
    - User: "exit" -> {"action": "exit", "parameters": {}}

Only respond with the JSON object representing the user's intent.
"""

class Colors:
    """ANSI color codes for prettier terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def samantha_speak(message):
    print(f"{Colors.CYAN}💬 {message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}{message}{Colors.ENDC}")

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base
)

conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

def get_action_from_model(user_input):
    """Sends user input to the AI and gets a structured JSON action back."""
    global conversation_history
    conversation_history.append({"role": "user", "content": user_input})

    try:
        chat_response = client.chat.completions.create(
            model = "Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
            messages = conversation_history,
            max_tokens = 256,
            temperature = 0.2,
            top_p = 0.9,
            response_format = {"type": "json_object"}
        )

        response_content = chat_response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": response_content})
        action_json = json.loads(response_content)
        return action_json
    
    except json.JSONDecodeError:
        print_error("Sorry, I received a malformed response from the AI. Please try again.")
        conversation_history.pop() # Remove the failed assistant message
        return None
    except Exception as e:
        print_error(f"An error occurred while communicating with the AI: {e}")
        conversation_history.pop() # Remove the failed assistant message
        return None

def handle_list_files(path="."):
    """Lists files and directories, distinguishing between them."""
    try:
        samantha_speak(f"Here's what I found in '{os.path.abspath(path)}': \n")
        items = os.listdir(path)
        if not items:
            print("  (This directory is empty)")
            return
        
        folders = sorted([item for item in items if os.path.isdir(os.path.join(path, item))])
        files = sorted([item for item in items if not os.path.isfile(os.path.join(path, item))])

        for folder_name in folders:
            print(f"  📁 {Colors.BLUE}{folder_name}/{Colors.ENDC}")
        for file_name in files:
            print(f"  📄 {file_name}")

    except FileNotFoundError:
        print_error(f"Directory not found: '{path}'")
    except PermissionError:
        print_error(f"I don't have permission to access '{path}'.")
    
def handle_change_directory(path):
    """Changes the current working directory."""
    if not path:
        print_error("You need to tell me which directory to go to.")
        return
    try:
        os.chdir(path)
        print_success(f"Changed directory to '{os.path.abspath(path)}'")
    except FileNotFoundError:
        print_error(f"Directory not found: '{path}'")
    except NotADirectoryError:
        print_error(f"'{path}' is not a directory.")
    except PermissionError:
        print_error(f"I don't have permission to access '{path}'.")

def handle_create_file(filename):
    """Creates a new empty file."""
    if not filename:
        print_error("You need to provide a name for the file.")
        return
    try:
        if os.path.exists(filename):
            print_error(f"File '{filename}' already exists.")
            return
        open(filename, 'a').close()
        print_success(f"Created file '{filename}'")
    except PermissionError:
        print_error(f"I don't have permission to create a file here.")
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")

def handle_create_directory(directory_name):
    """Creates a new directory."""
    if not directory_name:
        print_error("You need to provide a name for the folder.")
        return
    try:
        os.makedirs(directory_name)
        print_success(f"Created folder: {directory_name}")
    except FileExistsError:
        print_error(f"Directory '{directory_name}' already exists.")
    except PermissionError:
        print_error(f"I don't have permission to create a directory here.")

def handle_copy(source, destination):
    """Copies a file or directory."""
    if not source or not destination:
        print_error("You need to provide both source and destination.")
        return
    try:
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        print_success(f"Copied '{source}' to '{destination}'")
    except FileNotFoundError:
        print_error(f"Source '{source}' not found.")
    except FileExistsError:
        print_error(f"Destination '{destination}' already exists.")
    except PermissionError:
        print_error(f"I don't have permission to copy here.")
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")

def handle_move(source, destination):
    """Moves a file or directory."""
    if not source or not destination:
        print_error("I need both a source and a destination to move.")
        return
    try:
        shutil.move(source, destination)
        print_success(f"Moved '{source}' to '{destination}'.")
    except Exception as e:
        print_error(f"Could not move: {e}")

def handle_rename(source, destination):
    """Renames a file or directory."""
    handle_move(source, destination)

def handle_delete(path):
    """Deletes a file or directory with user confirmation."""
    if not path:
        print_error("I need to know what you want to delete.")
        return
    if not os.path.exists(path):
        print_error(f"'{path}' does not exist.")
        return

    print_warning(f"⚠️  You are about to permanently delete '{path}'.")
    confirm = input("Are you sure? [y/n]: ").lower().strip()

    if confirm == 'y':
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print_success(f"Deleted directory: {path}")
            else:
                os.remove(path)
                print_success(f"Deleted file: {path}")
        except Exception as e:
            print_error(f"Could not delete: {e}")
    else:
        samantha_speak("Okay, I've cancelled the deletion.")

def handle_find(name):
    """Finds a file or directory by exact name, searching recursively."""
    if not name:
        print_error("What file or folder are you looking for?")
        return
    
    samantha_speak(f"Searching for '{name}'...")
    results = []
    for root, dirs, files in os.walk("."):
        if name in dirs or name in files:
            results.append(os.path.join(root, name))
    
    if results:
        print_success("I found the following matches:")
        for res in results:
            print(f"  -> {res}")
    else:
        samantha_speak(f"Sorry, I couldn't find anything named '{name}'.")

def main():
    """The main loop for the Samantha assistant."""
    print(f"{Colors.HEADER}{Colors.BOLD}Welcome to Samantha, your OS assistant!{Colors.ENDC}")
    samantha_speak("How can I assist you today? (Type 'exit' to quit)")
    action_headers = {
        "list_files": handle_list_files,
        "change_directory": handle_change_directory,
        "create_file": handle_create_file,
        "create_directory": handle_create_directory,
        "copy": handle_copy,
        "move": handle_move,
        "rename": handle_rename,
        "delete": handle_delete,
        "find": handle_find,
        "exit": lambda: sys.exit(0)   
    }

    while True:
        try:
            current_dir = os.getcwd()
            prompt = f"\n{Colors.BOLD}💭 ({Colors.UNDERLINE}{current_dir}{Colors.ENDC}{Colors.BOLD}) What would you like to do?{Colors.ENDC} "
            user_input = input(prompt)

            if not user_input.strip():
                continue

            if user_input.lower().strip() in ["exit", "quit"]:
                samantha_speak("Goodbye!")
                break

            action_json = get_action_from_model(user_input)

            if action_json:
                action = action_json.get("action")
                params = action_json.get("parameters", {})

                if action in action_headers:
                    action_headers[action](**params)
                else:
                    print_error(f"Sorry, I don't know how to perform the action: '{action}'")
        except KeyboardInterrupt:
            samantha_speak("\nGoodbye!")
            break
        except Exception as e:
            print_error(f"An unexpected error occurred: {e}")

main()


        