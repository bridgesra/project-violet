import openai
import platform
if platform.system() != 'Windows':
    import pexpect
from Blue_Lagoon.honeypot_tools import stop_dockers, start_dockers
import config
import os

TIMEOUT = 40

openai.api_key = os.getenv('OPENAI_API_KEY')
openai_client = openai.OpenAI()

prompt_patterns = [pexpect.EOF, 
                    r'└─\x1b\[1;31m#',
                    r' \x1b\[0m> ', 
                    r'Are you sure you want to continue connecting \(yes/no/\[fingerprint\]\)\? ',
                    's password: ',
                    'Enter password: ',
                    r'\:\~\$ ',
                    "Please type 'yes', 'no' or the fingerprint: ",
                    "Do you want to install it? (N/y)",
                    "Overwrite (y/n)?",]

def start_ssh():
    ssh = pexpect.spawn('ssh -o StrictHostKeyChecking=no -p30' +  os.getenv('RUNID') +' root@localhost', encoding='utf-8')
    ssh.expect("root@localhost's password: ")
    ssh.sendline('toor')
    ssh.expect(r'└─\x1b\[1;31m#', timeout=60)
    ssh.before.strip()
    return ssh
    # except pexpect.exceptions.EOF:  # ONLY USE THIS WHEN RUNNING NO_RECONFIG
    #     print("Got EOF error, restarting dockers")
    #     stop_dockers()
    #     start_dockers()
    #     return start_ssh()

def send_terminal_command(connection, command):
    try:
        connection.send(command + "\r")
        connection.expect(prompt_patterns, timeout=TIMEOUT)
        if not connection.match or connection.match is pexpect.EOF:
            matched_pattern = ""
        elif connection.match is pexpect.EOF:
            print(f"Debug: Got an EOF.\n\tconnection.match = {connection.match}")
            matched_pattern = ""
        else:
            matched_pattern = connection.match.group(0)

        command_response = f"{connection.before.strip()}{matched_pattern}"
        return command_response
    except pexpect.exceptions.TIMEOUT:
        connection.sendline('\r')
        connection.expect(r'.*')
        matched_pattern = connection.match.group(0) if connection.match else ""
        command_response = f"{connection.before.strip()}{matched_pattern}***COMMAND TOOK TO LONG TO RUN, KILLING COMMAND***\n"
        connection.sendline('\r')
        connection.sendcontrol('c')
        connection.expect(prompt_patterns + [pexpect.TIMEOUT], timeout=5)
        matched_pattern = connection.match.group(0) if connection.match and connection.match is not pexpect.TIMEOUT else ""
        command_response2 = f"{connection.before.strip()}{matched_pattern}"

        return command_response + command_response2
    except UnicodeDecodeError:
        return connection.before.strip() # Maybe works?
        

command_messages = [
    {
        'role': 'system',
        'content': 'You are simulating a command execution system in Kali Linux. You will receive commands to run and you should respond with the output of the command as if it was executed in a terminal.'
    },
]

def terminal_input(command: str, ssh):
    """
        Run a command on the Kali Linux machine over SSH or simulate its execution with an LLM.
    """
    command_response = ""
    
    # Run command on Kali over SSH
    if not config.simulate_command_line:
        command_response = send_terminal_command(ssh, command)
        if len(command_response) > 10000:
            command_response = command_response[-10000:] + "\n***TOO LONG OUTPUT FROM COMMAND, ONLY SHOWING THE FINAL 10000 characters***"
        
        return command_response 

    # Simulate command execution
    else:
        command_messages.append({
            'role': 'user',
            'content': f'Run the command: {command}'
        })

        # send to OpenAI and get back the assistant message
        raw_resp = openai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=command_messages
        )
        msg = raw_resp.choices[0].message
        # extract content string and append
        command_text = msg.content
        command_messages.append({
            'role': 'assistant',
            'content': command_text
        })
        
    return command_text
    
    # return shell output in non-simulated or if simulate_execution is False
