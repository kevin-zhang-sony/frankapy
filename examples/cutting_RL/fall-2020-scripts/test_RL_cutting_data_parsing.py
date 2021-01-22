from frankapy.utils import *

#####################3########### load previous data and calculate updated policy and plot rewards
data_dir = '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/pivchop/carrot/exp_9/'
#policy_params_mean, policy_params_sigma = parse_policy_params_and_rews_from_file(data_dir,prev_epochs_to_calc_pol_update, hfpc = False)
policy_params_mean, policy_params_sigma = parse_policy_params_and_rews_from_file(data_dir, prev_epochs_to_calc_pol_update=10, hfpc = True)
import pdb; pdb.set_trace()
################################### plot multiple experiment rewards together on same plots
# normal cut
# work_dirs = ['/home/sony/Documents/cutting_RL_experiments/data/celery/normalCut/exp_9_posXZ_varStiff/',\
#     '/home/sony/Documents/cutting_RL_experiments/data/celery/normalCut/exp_8_posXforceZvarStiff/',
#         '/home/sony/Documents/cutting_RL_experiments/data/celery/normalCut/exp_7_genericRF/']
# work_dirs = ['/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/potato/exp_1/',\
#     '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/celery/exp_2/',\
#         '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/carrot/exp_3/']

# work_dirs = ['/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/banana/exp_4/',\
#     '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/tomato/exp_5/',\
#         '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/mozz/exp_6/']

# rews_or_avg_rews = 'rews'
# plot_rewards_mult_experiments(work_dirs, rews_or_avg_rews)

# rews_or_avg_rews = 'avg_rews'
# plot_rewards_mult_experiments(work_dirs, rews_or_avg_rews)

# # piv chop
# work_dirs = ['/home/sony/Documents/cutting_RL_experiments/data/celery/pivChop/exp_3_genericRF/',\
#     '/home/sony/Documents/cutting_RL_experiments/data/celery/pivChop/exp_4_forceZ_varStiff/']
# rews_or_avg_rews = 'rews'
# plot_rewards_mult_experiments(work_dirs, rews_or_avg_rews)

# rews_or_avg_rews = 'avg_rews'
# plot_rewards_mult_experiments(work_dirs, rews_or_avg_rews)

#################################### plot mean policy dmp trajectories from diff experiments
# work_dir = '/home/sony/Documents/cutting_RL_experiments/data/celery/normalCut/exp_9_posX_posZ_varStiff/'
# control_type_z_axis = 'position'
# position_dmp_weights_file_path = '/home/sony/092420_normal_cut_dmp_weights_zeroY.pkl'
# position_dmp_pkl = open(position_dmp_weights_file_path,"rb")
# init_dmp_info_dict = pickle.load(position_dmp_pkl)
# initial_wts = np.array(init_dmp_info_dict['weights'])

# epoch = 1
# dmp_traject_time = 5
# prev_epochs_to_calc_pol_update = 2
# policy_params_mean, policy_params_sigma = parse_policy_params_and_rews_from_file(work_dir, prev_epochs_to_calc_pol_update)
# REPS_updated_mean = policy_params_mean
# import pdb; pdb.set_trace()
# plot_updated_policy_mean_traject(work_dir, position_dmp_weights_file_path, epoch, dmp_traject_time, control_type_z_axis, init_dmp_info_dict, \
#     initial_wts, REPS_updated_mean)
# import pdb; pdb.set_trace()

########################################
# num_epochs = 3
# plot_rewards_mult_epochs(data_dir, num_epochs)

################################ parse force data
# # normal cut
# force_data_dir = '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/mozz/exp_6/forces_positions/'
# epoch = 2
# num_samples = 25
# max_z_forces_all_exp7 = viz_force_data(force_data_dir, epoch, num_samples)

# force_data_dir = '/home/sony/Documents/cutting_RL_experiments/data/celery/normalCut/exp_8_posX_forceZ_varStiff/forces_positions/'
# epoch = 2
# num_samples = 20
# max_z_forces_all_exp8 = viz_force_data(force_data_dir, epoch, num_samples)

# force_data_dir = '/home/sony/Documents/cutting_RL_experiments/data/celery/normalCut/exp_9_posX_posZ_varStiff/forces_positions/'
# epoch = 1
# num_samples = 20
# max_z_forces_all_exp9 = viz_force_data(force_data_dir, epoch, num_samples)

# # piv chop
# force_data_dir = '/home/sony/Documents/cutting_RL_experiments/data/celery/pivChop/exp_3_genericRF/forces_positions/'
# epoch = 1
# num_samples = 20
# max_z_forces_all_exp3 = viz_force_data(force_data_dir, epoch, num_samples)

# force_data_dir = '/home/sony/Documents/cutting_RL_experiments/data/celery/pivChop/exp_4_forceZ_varStiff/forces_positions/'
# epoch = 1
# num_samples = 20
# max_z_forces_all_exp4 = viz_force_data(force_data_dir, epoch, num_samples)

# plot task success metrics for multiple experiments
# work_dirs = ['/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/potato/exp_1/',\
#     '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/celery/exp_2/',\
#         '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/carrot/exp_3/',\
#             '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/banana/exp_4/',\
#     '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/tomato/exp_5/',\
#         '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/normal/mozz/exp_6/']

# food_types = ['potato', 'celery', 'carrot', 'banana', 'tomato','mozz']
# cut_types = ['normal']*6
# perc_succ_or_avg_succ = 'avg_succ' #'perc_succ'
# for i in range(len(food_types)):
#     work_dir = work_dirs[i]
#     food_type = food_types[i]
#     cut_type = cut_types[i]
#     print(food_type)
#     plot_mean_task_success_and_percent_success_cuts(work_dir, food_type, cut_type,perc_succ_or_avg_succ)
# plt.legend((food_types))
# plt.show()

############# plot UCB data for HL params
work_dirs = ['/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-controller-combo-exps/potato/normal/exp_8/',
    '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-controller-combo-exps/potato/pivchop/exp_3/',
    '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-controller-combo-exps/potato/scoring/exp_4/',
    '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-controller-combo-exps/tomato/normal/exp_5/',
    '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-controller-combo-exps/tomato/pivchop/exp_6/',
    '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-controller-combo-exps/tomato/scoring/exp_7/',
    ]
desc = ['potato-normal','potato-pivchop','potato-scoring','tomato-normal','tomato-pivchop','tomato-scoring']
for work_dir in work_dirs:
    plot_UCB_experiment_results(work_dir)
plt.legend((desc))
plt.show()
import pdb; pdb.set_trace()