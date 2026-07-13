from utils import run_subprocess

def check_updates():
	remote = run_subprocess(["git", "ls-remote", "origin", "main"], capture_output=True, text=True)
	remote = remote.stdout.strip()
	local = run_subprocess(["git", "show", "--format='%H'", "--no-patch"], capture_output=True, text=True)
	local = local.stdout.strip()
	return remote.split()[0], local.strip("'")

def update():
	remote, local = check_updates()
	if remote != local:
		run_subprocess(["git", "pull", "origin", "main"])