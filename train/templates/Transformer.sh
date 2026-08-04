# Transformer.sh — 상위 저장소에 없는 파일입니다.
#
# upstream/BatteryLife/train_eval_scripts/ 에 Transformer.sh 가 없습니다.
# models/Transformer.py 는 있으므로 CPTransformer.sh 를 그대로 베끼고
# model_name · --model_id · comment 셋만 바꿨습니다.
#
# 따라서 이 스크립트의 하이퍼파라미터는 CPTransformer 용으로 튜닝된
# 값입니다. Transformer 에 맞춰진 값이 아닙니다. 논문 조건이 아닙니다.
#
# 이 파일은 원본 형태의 템플릿입니다 (경로가 아직 /data/hwx/... 입니다).
# 실제 실행본은 .build/batterylife/Transformer_*.sh 입니다.

model_name=Transformer
dataset=MIX_large # MIX_large
train_epochs=100
early_cycle_threshold=100
learning_rate=0.00005
master_port=25216
num_process=2
batch_size=32
n_heads=4
seq_len=1
accumulation_steps=1
lstm_layers=6
e_layers=6
d_layers=4
d_model=128
d_ff=256
dropout=0
charge_discharge_length=300
patience=5 # Eearly stopping patience
lradj=constant
loss=MSE
seed=2024

checkpoints=/data/hwx/BL_new # the save path of checkpoints
data=Dataset_original
root_path=/data/trf/python_works/BatteryLife/dataset
comment='Transformer'
task_name=classification

CUDA_VISIBLE_DEVICES=2,3 accelerate launch --multi_gpu  --num_processes $num_process --main_process_port $master_port run_main.py \
  --task_name $task_name \
  --data $data \
  --is_training 1 \
  --root_path $root_path \
  --model_id Transformer \
  --model $model_name \
  --features MS \
  --seq_len $seq_len \
  --label_len 50 \
  --factor 3 \
  --enc_in 3 \
  --seed $seed \
  --dec_in 1 \
  --c_out 1 \
  --des 'Exp' \
  --itr 1 \
  --d_model $d_model \
  --d_ff $d_ff \
  --batch_size $batch_size \
  --learning_rate $learning_rate \
  --train_epochs $train_epochs \
  --model_comment $comment \
  --accumulation_steps $accumulation_steps \
  --charge_discharge_length $charge_discharge_length \
  --dataset $dataset \
  --num_workers 32 \
  --e_layers $e_layers \
  --lstm_layers $lstm_layers \
  --d_layers $d_layers \
  --patience $patience \
  --n_heads $n_heads \
  --early_cycle_threshold $early_cycle_threshold \
  --dropout $dropout \
  --lradj $lradj \
  --loss $loss \
  --checkpoints $checkpoints 

