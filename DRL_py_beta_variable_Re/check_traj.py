from glob import glob
import pandas as pd
import os


def check_trajectories(sample):
    """
    Check whether the trajectory is completed.
    In case trajectory fail to complete then delete specific trajectory.
    """

    traj_files = glob(f'./env/sample_{sample}' + "/*/")

    corrupted_traj = []
    completed_traj = []
    traj_i = []

    for i, traj in enumerate(traj_files):

        if os.path.isfile(traj_files[i] + "finished.txt") and len(completed_traj) < 30 and os.path.isfile(traj_files[i] + "trajectory.csv"):
            x_traj = pd.read_csv(traj_files[i] + "trajectory.csv", sep=",", header=0)
            t_l = len(x_traj.t.values)
            if t_l >= 399:
                completed_traj.append(traj)
                step = os.listdir(f'./env/sample_{sample}/trajectory_{i}/postProcessing/forces/')
                file_path = f"./env/sample_{sample}/trajectory_{i}/postProcessing/forces/" + step[0] + "/coefficient.dat"
                os.system(f"mkdir --parents ./Data/sample_{sample}/trajectory_{i}/; mv ./env/sample_{sample}/trajectory_{i}/trajectory.csv $_ ;mv {file_path} $_ &&"
                      f"rm -r {traj}")
            else:
                corrupted_traj.append(traj)
                traj_i.append(i)
            
        else:
            corrupted_traj.append(traj)
            traj_i.append(i)
   
    for i, traj in enumerate(corrupted_traj):
        os.system(f"mkdir --parents ./failed/sample_{sample}/{traj_i[i]}/; mv {traj}/* $_ &&"
                  f"rm -r {traj}")