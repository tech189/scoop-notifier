import ast
import subprocess
from pathlib import Path
from win10toast import ToastNotifier
import argparse
import logging, sys

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter("%(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def print_status():
    task_query = subprocess.check_output(["schtasks", "/query"], shell=True).decode("utf-8")

    if "Scoop notifier" in task_query:
        task_interval = subprocess.check_output(["powershell", "[System.Xml.XmlConvert]::ToTimeSpan((Get-ScheduledTask \"Scoop notifier\").Triggers.Repetition.Interval).totalhours"]).decode("utf-8").strip()
        print(f"✅ Scoop notifier task installed to run every {task_interval} hours")
    else:
        # TODO default to checking every 24 hours with nargs in argparse
        print("❌ Scoop notifier task not installed\n\tInstall it with --install.")

def create_task(interval):
    # scoop-notifier
    notifier_dir = Path(__file__).parent.parent.resolve()
    # scoop-notifier/scoop_notifier
    notifier_scripts_dir = Path(__file__).parent.resolve()
    # scoop-notifier/scoop_notifier/notifier.py
    notifier_path = Path(__file__).resolve()
    # scoop-notifier/scoop_notifier/notifier-batch.cmd
    notifier_batch_path = notifier_scripts_dir.joinpath("notifier-batch.cmd")
    # scoop-notifier/scoop_notifier/notifier-silent.vbs
    notifier_silent_path = notifier_scripts_dir.joinpath("notifier-silent.vbs")

    logging.debug(f"\nnotifier_dir\t{notifier_dir}\nnotifier_scripts_dir\t{notifier_scripts_dir}\nnotifier_path\t{notifier_path}\nnotifier_batch_path\t{notifier_batch_path}\nnotifier_silent_path\t{notifier_silent_path}")

    # if not Path(notifier_batch_path).exists():
    try:
        with open(notifier_batch_path, "w") as file:
            # TODO to be converted to python -m when released as module
            file.write(f"cd /d \"{notifier_dir}\" && poetry run python \"{notifier_path}\" --check\n")
        with open(notifier_silent_path, "w") as file:
            file.write(f"Dim WinScriptHost\nSet WinScriptHost = CreateObject(\"WScript.Shell\")\nWinScriptHost.Run Chr(34) & \"{notifier_batch_path}\" & Chr(34), 0\nSet WinScriptHost = Nothing\n")
        print("✅ Task files successfully written")
    except:
        print("❌ Failed to create task files, check permissions")
    # else:
    #     print("⏩ Task files already exist, skipping")
    
    # task_query = subprocess.check_output(["schtasks", "/query"], shell=True).decode("utf-8")

    # if "Scoop notifier" not in task_query:
    try:
        subprocess.run(["powershell", "-NoProfile", f"$taskName = \"Scoop notifier\";if (Get-ScheduledTask | Where-Object {{$_.TaskName -like $taskName}}) {{Unregister-ScheduledTask -TaskName $taskName -Confirm:$false}};$action = New-ScheduledTaskAction -Execute 'wscript' -Argument '\"{notifier_silent_path}\"';$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date) + (New-TimeSpan -Minutes 1)) -RepetitionInterval (New-TimeSpan -Minutes {interval});Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $taskName -Description \"Check for scoop app updates\""], capture_output=True)
        print("✅ Task successfully scheduled")
        task_interval = subprocess.check_output(["powershell", "-NoProfile", "[System.Xml.XmlConvert]::ToTimeSpan((Get-ScheduledTask \"Scoop notifier\").Triggers.Repetition.Interval).totalhours"]).decode("utf-8").strip()
        print(f"✅ Scoop notifier will check for updates every {task_interval} hours")
    except:
        print("❌ Task could not be scheduled")
    # else:
    #     print("⏩ Task already scheduled, skipping")

def remove_task():
    task_query = subprocess.check_output(["schtasks", "/query"], shell=True).decode("utf-8")

    if "Scoop notifier" in task_query:
        try:
            subprocess.run(["powershell", "-NoProfile", "$taskName = \"Scoop notifier\";Unregister-ScheduledTask -TaskName $taskName -Confirm:$false"], capture_output=True)
            print("✅ Task successfully removed")
        except:
            print("❌ Task could not be removed, delete manually in Task Scheduler")
    else:
        print("⏩ Task not scheduled, skipping")

def check_now():
    scoop_path = Path.home().joinpath("scoop\\shims\\scoop")
    bucket_dir = Path.home().joinpath("scoop\\buckets")

    logging.debug(f"scoop_path:\t{scoop_path}\nbucket_dir\t{bucket_dir}")

    subprocess.run([scoop_path, "update"], shell=True)
    scoop_status = subprocess.getoutput("pwsh.exe -Command \"Set-Location " + str(scoop_path.parent) + "; .\scoop status | Select-Object -Expand Name | Join-String -Separator ',' -OutputPrefix 'Updates are available for: [' -OutputSuffix ']' -DoubleQuote\"")

    counter = 0
    updates = []
    for line in scoop_status.splitlines():
        if line[0:26] == ("Updates are available for:"):
            updates = ast.literal_eval(line[26:])  

    notifier = ToastNotifier()
    update_count = len(updates)
    bucket_count = len(list(bucket_dir.glob('*')))

    if updates == []:
        # TODO give option to show this, but off by default
        notifier.show_toast("No updates available", str(bucket_count) + " buckets checked", duration = 5)
        exit()
    elif "Update failed." in scoop_status:
        # TODO give option to show this, but off by default
        # TODO also show this when "Update failed." appears in check variable - even if updates available in scoop status, if no internet connection then updates won't install
        notifier.show_toast("Error updating", "😢 No internet connection", duration = 5)
        exit()
    else:
        if update_count > 1:
            update_message = "📦 " + str(update_count) + " updates available"
        else:
            update_message = "📦 1 update available"
        try:
            notifier.show_toast(update_message, "Scoop is ready to update " + ", ".join(updates), duration = None, icon_path = None)
        except TypeError:
            # normal, this is a hack to keep the notification in the Action Centre after using duration = None
            exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatic update checker for apps installed with scoop")
    parser.add_argument("--install", help="add update check to task scheduler")
    parser.add_argument("--uninstall", help="remove update check from task scheduler", action="store_true")
    parser.add_argument("--check", help="check for updates now", action="store_true")
    parser.add_argument("--debug", help="print variables for debugging", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    if args.install:
        create_task(args.install)
    elif args.uninstall:
        remove_task()
    elif args.check:
        check_now()
    else:
        print_status()