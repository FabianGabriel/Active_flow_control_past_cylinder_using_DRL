"""
    This file to run trajectory, hence handling OpenFOAM files and executing them in machine

    called in : replay_buffer.py
"""

import _thread
import os
import queue
import subprocess
import time
import random

import numpy as np


class env:
    """
        This Class is to run trajectory, hence handling OpenFOAM files and executing them in machine
    """
    def __init__(self, n_worker, buffer_size, control_between):
        """

        Args:
            n_worker: no of trajectories at the same time (worker)
            buffer_size: total number of trajectories
            contol_between: random starting point range of action in trajectory
        """
        self.n_worker = n_worker
        self.buffer_size = buffer_size
        self.control_between = control_between

    def write_jobfile(self, core_count, job_name, file, job_dir):
        with open(f'{job_dir}/jobscript.sh', 'w') as rsh:
            rsh.write(f"""#!/bin/bash -l        
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --time=01:10:00
#SBATCH --job-name={job_name}
#SBATCH --ntasks-per-node={core_count}

module load singularity/3.6.0rc2
module load mpi/openmpi/4.0.1/cuda_aware_gcc_6.3.0

cd {job_dir}

./Allrun.singularity

touch finished.txt""")

        os.system(f"chmod +x {job_dir}/jobscript.sh")

    def rand_n_to_contol(self, re):
        """
        To get the random number from the range -> .2f%

        Args:
            re: choosen reynolds number

        Returns: random number

        """
        n_rand = np.random.uniform(self.control_between[re][0], self.control_between[re][1], 1)
        n_rand = np.round(n_rand, 2)
        return n_rand

    def process_waiter(self, proc, job_name, que):
        """
             This method is to wait for the executed process till it is completed
         """
        try:
            proc.wait()
        finally:
            que.put((job_name, proc.returncode))

    def run_trajectory(self, buffer_counter, proc, results, sample, action_bounds, re_choosen):
        """
        To run the trajectories

        Args:
            buffer_counter: which trajectory to run (n -> traj_0, traj_1, ... traj_n)
            proc: array to hold process waiting flag
            results: array to hold process finish flag
            sample: number of iteration of main ppo
            action_bounds: min and max omega value
            re_choosen: choosen reynolds numbers

        Returns: execution of OpenFOAM Allrun file in machine

        """
        # number of cores
        core_count = 4

        # choose reynolds number
        zeros = '.2f'

        if re_choosen == 100:
            # get the random start
            rand_control_traj = self.rand_n_to_contol(0)

            # changing of end time to keep trajectory length equal
            endtime = round(float(rand_control_traj[0] + 2), 2)

            time_string = f"{rand_control_traj[0]:,{zeros}}025"
            deltaT = 2.5e-4
        elif re_choosen == 200:
            # get the random start
            rand_control_traj = self.rand_n_to_contol(1)

            # changing of end time to keep trajectory length equal
            endtime = round(float(rand_control_traj[0] + 1), 2)

            time_string = f"{rand_control_traj[0]:,{zeros}}0125"
            deltaT = 1.25e-4
        else:
            # get the random start
            rand_control_traj = self.rand_n_to_contol(2)

            # changing of end time to keep trajectory length equal
            endtime = round(float(rand_control_traj[0] + 0.5), 2)

            time_string = f"{rand_control_traj[0]:,{zeros}}00625"
            deltaT = 0.625e-4

        # make dir for new trajectory
        traj_path = f"./env/sample_{sample}/trajectory_{buffer_counter}"

        print(f"\n starting trajectory : {buffer_counter} \n")
        os.makedirs(traj_path, exist_ok=True)

        # copy files form base_case
        # change starting time of control -> 0.org/U && system/controlDict
        # change of ending time -> system/controlDict
        os.popen(f'cp -r ./env/base_case/agentRotatingWallVelocity/* {traj_path}/ && '
                 f'sed -i "s/startTime.*/startTime       {rand_control_traj[0]};/g" {traj_path}/0/U &&'
                 f'sed -i "s/absOmegaMax.*/absOmegaMax       {action_bounds[1]};/g" {traj_path}/0/U &&'
                 f'sed -i "s/startTime.*/startTime       {rand_control_traj[0]};/g" {traj_path}/0.org/U &&'
                 f'sed -i "s/absOmegaMax.*/absOmegaMax       {action_bounds[1]};/g" {traj_path}/0.org/U &&'
                 f'sed -i "/^endTime/ s/endTime.*/endTime         {endtime};/g" {traj_path}/system/controlDict &&'
                 f'sed -i "s/timeStart.*/timeStart       {rand_control_traj[0]};/g" {traj_path}/system/controlDict &&'
                 f'sed -i "s/deltaT.*/deltaT       {deltaT};/g" {traj_path}/system/controlDict &&'
                 f'sed -i "s/magUInf.*/magUInf       {re_choosen/100};/g" {traj_path}/system/controlDict &&'
                 f'sed -i "s/Um .*/Um       {re_choosen/100*1.5};/g" {traj_path}/system/setExprBoundaryFieldsDict')
        
        for i in range(core_count):
            while not os.path.exists(f'{traj_path}/processor{i}//0.00025'):
                time.sleep(1)
            os.popen(f'cp -r ./env/base_case/baseline_data/Re_{re_choosen}/processor{i}/{time_string} {traj_path}/processor{i}/{time_string} &&'
                 f'sed -i "s/startTime.*/startTime       {rand_control_traj[0]};/g" {traj_path}/processor{i}/0.00025/U &&'
                 f'sed -i "s/startTime.*/startTime       {rand_control_traj[0]};/g" {traj_path}/processor{i}/{time_string}/U &&'
                 f'sed -i "s/absOmegaMax.*/absOmegaMax       {action_bounds[1]};/g" {traj_path}/processor{i}/0.00025/U &&'
                 f'sed -i "s/absOmegaMax.*/absOmegaMax       {action_bounds[1]};/g" {traj_path}/processor{i}/{time_string}/U &&'
                 f'sed -i "s/train.*/train       {1};/g" {traj_path}/processor{i}/0.00025/U &&'
                 f'sed -i "s/train.*/train       {1};/g" {traj_path}/processor{i}/{time_string}/U')

        self.write_jobfile(core_count, job_name=f'traj_{buffer_counter}', file='./Allrun', job_dir=traj_path+'/')
        jobfile_path = f'{traj_path}' + '/jobscript.sh'

        proc[buffer_counter] = subprocess.Popen(['sh', 'submit_job.sh', jobfile_path])
        _thread.start_new_thread(self.process_waiter,
                                 (proc[buffer_counter], f"trajectory_{buffer_counter}", results))

    def sample_trajectories(self, sample, action_bounds, re):
        """

        Args:
            sample: main ppo iteration counter
            action_bounds: min and max omega value
            re: possible reynolds numbers

        Returns: execution of n number of trajectory (n = buffer_size)

        """
        # set the counter to count the numbre of trajectory
        buffer_counter = 0

        # list for the status of trajectory running or finished
        proc = []

        # set the n_workers
        for t in range(int(max(self.buffer_size, self.n_worker))):
            item = "proc_" + str(t)
            proc.append(item)

        # get status of trajectory
        results = queue.Queue()
        process_count = 0
        re_choosen = 0

        # execute the n = n_workers trajectory simultaneously
        for n in np.arange(self.n_worker):
            if process_count < self.n_worker / 3:
                re_choosen = re[0]
            elif process_count < self.n_worker * 2 / 3:
                re_choosen = re[1]
            else:
                re_choosen = re[2]
            self.run_trajectory(buffer_counter, proc, results, sample, action_bounds, re_choosen)
            process_count += 1
            # increase the counter of trajectory number
            buffer_counter += 1

        # check for any worker is done. if so give next trajectory to that worker
        while process_count > 0:
            job_name, rc = results.get()
            print("job : ", job_name, "finished with rc =", rc)
            if self.buffer_size > buffer_counter:
                self.run_trajectory(buffer_counter, proc, results, sample, action_bounds, re)
                process_count += 1
                buffer_counter += 1
            process_count -= 1


if __name__ == "__main__":
    n_worker = 2
    buffer_size = 4
    control_between = [0.1, 4]
    sample = 0
    env = env(n_worker, buffer_size, control_between)
    env.sample_trajectories(sample)
