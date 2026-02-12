rule test_gpu:
    # output:
    #     # "test_gpu.txt"
    # resources:
    #     gpu=1
    conda:
        "chrombpnet"
    shell:
        """
        python - <<EOF
import tensorflow as tf
print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))
EOF
        """