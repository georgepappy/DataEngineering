eval `ssh-agent -s`
ssh-add -l -E sha256
ssh -T git@github.com

git -C /Users/georgepappy/Documents/Metis/online_flex/Module7_DataEngineering/project_sandbox/tracker_1/ add .
git -C /Users/georgepappy/Documents/Metis/online_flex/Module7_DataEngineering/project_sandbox/tracker_1/ commit -m "Daily database update (new data)"
git -C /Users/georgepappy/Documents/Metis/online_flex/Module7_DataEngineering/project_sandbox/tracker_1/ push -u origin main
