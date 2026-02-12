if [ -z "$SLURM_JOB_ID" ]; then
    echo "RUNNING LOCALLY"
else
    echo "RUNNING ON SLURM"
    module load system pango cairo
fi