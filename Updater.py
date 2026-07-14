from utils import run_subprocess

def check_updates(version="main"):
	remote = run_subprocess(["git", "ls-remote", "origin", version], capture_output=True, text=True)
	remote = remote.stdout.strip()
	local = run_subprocess(["git", "show", "--format='%H'", "--no-patch"], capture_output=True, text=True)
	local = local.stdout.strip()
	return remote.split()[0], local.strip("'")

def update(version="main"):
	remote, local = check_updates(version)
	if remote != local:
		run_subprocess(["git", "pull", "origin", version], capture_output=True, text=True)