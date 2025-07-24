from Red.terminal_io import start_ssh, send_terminal_command


ssh = start_ssh()

output = send_terminal_command(ssh, "apt upgrade -y")

print(output)