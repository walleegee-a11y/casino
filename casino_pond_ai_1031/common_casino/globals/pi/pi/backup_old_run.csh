#! /usr/bin/csh -f

set completed_file = "completed_tasks___${stage}.yaml"

if (-e ../$completed_file && `find | wc -l` >= 5) then
	cd ..
	set completed_date = `grep "start_time" $completed_file | awk '{print $2}' | awk -F / '{print $1$2$3}' | cut -c 3-`
	set completed_time = `grep "start_time" $completed_file | awk '{print $3}' | awk -F : '{print $1$2$3}' | cut -c -4`
	echo "$completed_date - $completed_time"
	set backup_dir = "${stage}_${completed_date}_${completed_time}"
	mkdir -p .backup
	mv $stage .backup/$backup_dir
	echo "move dir $stage to ./.backup/$backup_dir"

	mkdir $stage
	cd $stage
	cp ../.backup/$backup_dir/all_tools_env.csh .
	cp ../.backup/$backup_dir/env_vars.csh .
	if ($stage == "sta_pt") then
		mkdir dmsa
	endif
endif
