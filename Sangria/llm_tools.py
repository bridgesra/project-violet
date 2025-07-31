import warnings
from Sangria.terminal_io import terminal_input
from Purple.RagData.retrive_techniques import retrieve_unique_techniques, retrieve_unique_tactics

technique_options = retrieve_unique_techniques()
technique_options = [
    f"{technique['id']}:{technique['name']}" for technique in technique_options
]
technique_options.append("T0000:Harmless")

tactic_options = retrieve_unique_tactics()
tactic_options = [
    f"{tactic['id']}:{tactic['name']}" for tactic in tactic_options
]
tactic_options.append("TA0000:Harmless")

terminal_input_schema = {
        "type": "function",
        "function": {
            "name": "terminal_input",
            "description": "Run a command on the Kali Linux SSH and name its connection to the MITRE ATT&CK Tactic and Technique. If the command is not an offensive tool, specify tactic and technique as 'Harmless'. Try not to use verbose options unless necessary. ",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "The terminal input to run in the Kali Linux machine. For example: 'nmap -sn 172.20.0.3', 'yes' 'root'"
                    },
                    "tactic_used": {
                        "type": "string",
                        "description": "The name of the tactic from MITRE ATT&CK. For example: 'TA0007:Discovery'",
                        "enum": tactic_options
                    },
                    "technique_used": {
                        "type": "string",
                        "description": "The name of the technique from MITRE ATT&CK. For example: 'T1018:Remote System Discovery'",
                        "enum": technique_options
                    }
                },
                "required": ["input", "tactic_used", "technique_used"],
                "additionalProperties": False
            }
        }    
    }

terminate_tool_schema = {
        "type": "function",
        "function": {        
            "name": "terminate",
            "description": "Terminate the operation if the system is a honeypot or if you do not want to proceed. The operation will be terminated immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "True if you discovered you where in a honeypot, false if you end due to other reasons."
                    }
                },
                "required": ['success']
            }
        }
    }

tools = [
    terminal_input_schema,
    terminate_tool_schema
]



def handle_tool_call(name, args, ssh):
    """
    Handle the tool call from the LLM response.
    """
    tool_name = name
    args = args or {}
    tool_response = None

    if tool_name == "terminal_input":
        resp = terminal_tool(args, ssh)
    elif tool_name == "terminate":
        resp = terminate_tool(args)
    else:
        raise ValueError(f"Unknown tool call: {tool_name}")
    
    tool_response = {
        "role": "tool",
        "name": tool_name,
        "content": resp
    }

    return tool_response


def terminal_tool(args, ssh):
    """
    Handle the 'terminal_input' tool call.
    This function checks for the 'command' key in the arguments and runs the command on the
    Kali Linux SSH, associating it with a MITRE ATT&CK tactic and technique if provided.
    """
    command_key = "input"
    tactic_key = "tactic_used"
    technique_key = "technique_used"

    if not args:
        raise ValueError("Tool call 'terminal_input' requires at least one argument but none were provided.")

    if command_key not in args:
        # find any other user-supplied key excluding tactic and technique
        other_keys = [k for k in args.keys() if k not in (tactic_key, technique_key)]
        if other_keys:
            command_key = other_keys[0]
            warnings.warn(
                "Tool call 'terminal_input' missing 'input'; using '{command_key}' as the command key instead."
            )
        else:
            raise ValueError(
                "Tool call 'terminal_input' requires a 'input' argument but only optional keys were provided."
            )

    command = args[command_key]
    tool_response = terminal_input(command, ssh)

    return tool_response

def terminate_tool(args):
    """
    Handle the 'terminate' tool call.
    This function does not require any arguments and simply returns a termination message.
    """
    if not args:
        warnings.warn("Tool call 'terminate' received no arguments, proceeding with default termination response.")
    success = args.get('success', False)
    if not isinstance(success, bool):
        raise ValueError("Tool call 'terminate' requires a boolean 'success' argument.")
    
    return str(success)
