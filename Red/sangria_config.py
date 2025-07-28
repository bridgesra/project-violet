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

terminal_input = {
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

terminate_tool = {
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
    terminal_input,
    terminate_tool
]
