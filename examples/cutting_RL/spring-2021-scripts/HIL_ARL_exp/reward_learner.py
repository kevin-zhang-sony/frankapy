

from rl_utils import reps
import numpy as np 
import matplotlib.pyplot as plt 
import sklearn.gaussian_process as gp
from scipy.stats import multivariate_normal
import sklearn
import copy 

import sys
import os
import pprint
import torch.nn as nn
# from torchvision.transforms import functional as F
import torch.optim as optim
import gpytorch
import torch
import time
import json
import copy
from tqdm import tqdm
from sklearn.metrics import f1_score
from scipy.stats import norm
from gp_regression_model import GPRegressionModel

from policy_learner import REPSPolicyLearner

     
class RewardLearner:
    '''Reward_Learner for ARL using GPytorch for GP implementation 
    '''
    def __init__(self, work_dir, kappa, cut_type, food_type, desired_cutting_behavior):
        self.work_dir = work_dir
        self.kappa = kappa #EPD sampling threshold
        self.scale_pol_params = None
        self.add_ridge_to_pol_cov = True
        self.sampl_or_weight_kld_calc = None #'sampling' or 'weight'
        self.n_GP_training_samples = None
        self.cut_type = cut_type
        self.food_type = food_type
        self.desired_cutting_behavior = desired_cutting_behavior

    def plot_rewardModel_vs_oracle_rewards(self, reward_model_rewards_all_mean_buffer, automated_expert_rewards_all):
        plt.plot(reward_model_rewards_all_mean_buffer)
        plt.plot(automated_expert_rewards_all)
        plt.title('expert rewards vs reward model rewards')
        plt.legend(('GP reward model rewards', 'oracle expert rewards'))
        plt.show()

    def remove_already_queried_samples_from_list(self, samples_to_query, queried_samples_all):
        num_samples = len(samples_to_query)
        samples_to_query_new = copy.deepcopy(samples_to_query)        
        for i in range(0, num_samples):
            if samples_to_query[i] in queried_samples_all:
                samples_to_query_new.remove(samples_to_query[i])
        return samples_to_query_new

    def convert_list_outcomes_to_array(self, outcomes_list):
        import pdb; pdb.set_trace()
        num_samples = len(outcomes_list)
        num_features = len(outcomes_list[0])
        outcomes_arr = np.zeros((num_samples, num_features))
        for i in range(0,len(outcomes_list)):
            outcomes_arr[i,:] = np.array(outcomes_list[i])
        return outcomes_arr
    
    def query_expert_rewards_and_update_GP_training_data(self, epoch, GP_training_data_x_all, GP_training_data_y_all, \
        samples_to_query, queried_outcomes, expert_rewards_all_epochs):

        if samples_to_query!=[]:
            print('querying samples: ', samples_to_query)
            # import pdb; pdb.set_trace()       
            if self.desired_cutting_behavior == 'slow' or self.desired_cutting_behavior == 'fast':
                queried_expert_rewards_slow = (np.array(expert_rewards_all_epochs)[samples_to_query, 0])
                queried_expert_rewards_fast = (np.array(expert_rewards_all_epochs)[samples_to_query, 1])

                if self.desired_cutting_behavior == 'slow':
                    queried_expert_rewards = queried_expert_rewards_slow

                elif self.desired_cutting_behavior == 'fast':
                    queried_expert_rewards = queried_expert_rewards_fast
           
            else:
                queried_expert_rewards = np.array(expert_rewards_all_epochs)[samples_to_query]
            #import pdb; pdb.set_trace()
        
        else: 
            print('No samples to query from human')
        
        '''save all queried outcomes and queried rewards in buffer to send to GPytorch model as training data everytime it get updated:
        train_x is queried_outcomes ((nxD) arr), train_y is queried_expert_rewards ((n,) arr)'''

        # stack reward features (GP model x training data)
        GP_training_data_x_all = np.vstack((GP_training_data_x_all, queried_outcomes))
        print('shape GP_training_data_x_all', GP_training_data_x_all.shape)
        #import pdb; pdb.set_trace()

        # get GP model y training data (expert rewards) based on desired cutting behavior
        if self.desired_cutting_behavior == 'slow':
            GP_training_data_y_all = np.concatenate((GP_training_data_y_all, queried_expert_rewards_slow))
            np.savez(self.work_dir + '/' 'GP_reward_model_data/' + 'GP_reward_model_training_data_slowCut_epoch_'+str(epoch) + '.npz', GP_training_data_x_all = GP_training_data_x_all, \
                        GP_training_data_y_all = GP_training_data_y_all)
            

        elif self.desired_cutting_behavior == 'fast':        
            GP_training_data_y_all = np.concatenate((GP_training_data_y_all, queried_expert_rewards_fast))    
            np.savez(self.work_dir + '/' 'GP_reward_model_data/' + 'GP_reward_model_training_data_fastCut_epoch_'+str(epoch) + '.npz', GP_training_data_x_all = GP_training_data_x_all, \
                        GP_training_data_y_all = GP_training_data_y_all)
            
            #import pdb; pdb.set_trace()           
        
        else:
            GP_training_data_y_all = np.concatenate((GP_training_data_y_all, queried_expert_rewards))
            np.savez(self.work_dir + '/' 'GP_reward_model_data/' + 'GP_reward_model_training_data_qualityCut_epoch_'+str(epoch) + '.npz', GP_training_data_x_all = GP_training_data_x_all, \
                    GP_training_data_y_all = GP_training_data_y_all)
            #import pdb; pdb.set_trace()
        
        print('GP_training_data_x_all', GP_training_data_x_all.shape)
        print('GP_training_data_y_all', GP_training_data_y_all.shape)
        #import pdb; pdb.set_trace()          

        return GP_training_data_x_all, GP_training_data_y_all, queried_expert_rewards
        
    
    def save_reward_learning_data_to_np_arrays(self, work_dir, time_to_complete_cut, task_success, \
        task_success_more_granular, reward_features_all_samples, expert_rewards_all_epochs, training_data_list):
        # save training data list  
        np.save(work_dir + '/' + 'GP_reward_model_data/' + 'training_data_list.npy', np.array(training_data_list))
        # save expert rewards all epochs
        np.save(work_dir + '/' + 'GP_reward_model_data/' + 'expert_rewards_all_epochs.npy', np.array(expert_rewards_all_epochs))  

        # save task success metrics           
        np.save(os.path.join(work_dir, 'cut_times_all_samples.npy'), np.array(time_to_complete_cut))
        np.save(os.path.join(work_dir, 'task_success_all_samples.npy'), np.array(task_success)) 
        np.save(os.path.join(work_dir, 'task_success_more_granular_all_samples.npy'), np.array(task_success_more_granular))
        # save reward features each samples
        np.save(os.path.join(work_dir, 'reward_features_all_samples.npy'), np.array(reward_features_all_samples))
       

    def compute_KL_div_sampling_updated(self, agent, num_samples, pi_tilda_mean, pi_tilda_cov, \
        pi_star_mean, pi_star_cov, initial_wts, cut_type, S): #taking samples from policies pi_star and pi_tilda
        sampled_params_pi_tilda, sampled_params_pi_star = [], []

        # ADDING TO DEBUG NUM INSTAB
        if self.add_ridge_to_pol_cov:
            pi_tilda_cov = pi_tilda_cov + np.eye(pi_tilda_cov.shape[0])*5 #2
            pi_star_cov = pi_star_cov + np.eye(pi_tilda_cov.shape[0])*5 #2       
        
        for i in range(0, num_samples):
            new_params_pi_tilda = agent.sample_new_params_from_policy_only_mu_sigma(self.scale_pol_params, pi_tilda_mean, pi_tilda_cov, initial_wts, cut_type, S)
            new_params_pi_star = agent.sample_new_params_from_policy_only_mu_sigma(self.scale_pol_params, pi_star_mean, pi_star_cov, initial_wts, cut_type, S)
            #import pdb; pdb.set_trace()

            sampled_params_pi_tilda.append(new_params_pi_tilda)
            sampled_params_pi_star.append(new_params_pi_star)

        sampled_params_pi_tilda = np.array(sampled_params_pi_tilda)
        sampled_params_pi_star = np.array(sampled_params_pi_star)

        pi_star_wi = multivariate_normal.pdf(sampled_params_pi_star, mean=pi_star_mean, cov=pi_star_cov, allow_singular=True)
        # originally sampling from pi_tilda but not doing importance sampling ... need to fix!
        pi_tilda_wi = multivariate_normal.pdf(sampled_params_pi_tilda, mean=pi_tilda_mean, cov=pi_tilda_cov, allow_singular=True)

        star_div_tilda = (pi_star_wi/pi_tilda_wi)
        disc_prob = (pi_star_wi + pi_tilda_wi)/2

        # debug
        tilda_vals,tilda_vecs = np.linalg.eig(pi_tilda_cov)
        star_vals,star_vecs = np.linalg.eig(pi_star_cov)
        print('tilda_vals', tilda_vals)
        print('star_vals', star_vals)

        approx_sampling_KLdiv = (1/num_samples)*np.sum((pi_star_wi/disc_prob)*np.log(star_div_tilda))
        #approx_sampling_KLdiv = (1/num_samples)*np.sum(pi_star_wi*np.log(star_div_tilda))
        #approx_sampling_KLdiv = (1/num_samples)*np.sum(star_div_tilda*np.log(star_div_tilda))

        # import pdb; pdb.set_trace()
        return approx_sampling_KLdiv
   
           
    def train_GPmodel(self, work_dir, num_epochs, optimizer, model, likelihood, mll, train_x, train_y):
        self.work_dir = work_dir 
        print('training model')    
        #import pdb; pdb.set_trace()
        model.train()
        likelihood.train()
        for epoch in range(num_epochs):
            # Zero backprop gradients
            optimizer.zero_grad()
            # Get output from model
            output = model(train_x) #output.mean and output.variance returns mean and var of model
            # Calc loss and backprop derivatives
            loss = -mll(output, train_y)        
            loss.backward()

            # only print this info if we're training/updating GP model, not when computing EPD
            if num_epochs > 10:
                print('GP Model Training Epoch%d, Loss:%.3f, scale:%.3f' % (epoch, loss.item(), model.covar_module.outputscale.item()))
                # print updated covar matrix 
                if epoch % 20 == 0:
                #print('updated covariance matrix', output.lazy_covariance_matrix.evaluate())
                    print('model noise', model.likelihood.noise.item())
                #   save updated covariance_matrix
                    covmat_np = output.lazy_covariance_matrix.evaluate().detach().numpy()
                    np.savetxt(work_dir + '/' + 'GP_reward_model_data' + '/' + 'GP_cov_mat/' + 'epoch%i_numTrainSamples%i.txt'%(epoch, train_x.shape[0]), covmat_np)

            optimizer.step() #updates lengthscale, signal variance, AND g NN weights
        print('updated lengthscale: ', model.covar_module.base_kernel.lengthscale)
        print('updated outputscale: ', model.covar_module.outputscale)
        print('updated covariance matrix', output.lazy_covariance_matrix.evaluate())
        print('done training')

        self.num_reward_features = model.num_features
        # import pdb; pdb.set_trace()
        return model

    def calc_expected_reward_for_observed_outcome_w_GPmodel(self, model, likelihood, new_outcomes):
        # import pdb; pdb.set_trace()
        # convert new_outcomes data to torch tensor
        if type(new_outcomes)==np.ndarray: 
            if len(new_outcomes.shape) == 1:
                new_outcomes =  np.expand_dims(new_outcomes, axis=0) # expand dims to be 1xn
            new_outcomes = torch.from_numpy(new_outcomes)
            new_outcomes = new_outcomes.float()
        model.eval()
        likelihood.eval()
        print('evaluating model')
        mean_expected_rewards, var_expected_rewards =[], [] 
        with torch.no_grad(), gpytorch.settings.use_toeplitz(False):         
            #import pdb; pdb.set_trace()     
            preds = model(new_outcomes)
            mean_expected_rewards = preds.mean.numpy().tolist()
            var_expected_rewards = preds.variance.numpy().tolist()
            #print('updated covariance matrix', preds.lazy_covariance_matrix.evaluate())
        
        # import pdb; pdb.set_trace()
        
        # import pdb; pdb.set_trace()
        return mean_expected_rewards, var_expected_rewards
    
    # def calc_PI_all_outcomes(self, prior_training_data, queried_samples_all, lambda_thresh, eps=0.01, beta = 0.5):
    #     prior_training_data_expect_rewards_mean, prior_training_data_policy_params, \
    #         prior_training_data_expect_rewards_sig = [], [], []        
    #     prior_training_data_o = np.empty([0,self.num_reward_features])
        
    #     for i in range(len(prior_training_data)):
    #         prior_training_data_o = np.vstack((prior_training_data_o, prior_training_data[i][0]))
    #         prior_training_data_expect_rewards_mean.append(prior_training_data[i][1])
    #         prior_training_data_expect_rewards_sig.append(prior_training_data[i][2])
    #         prior_training_data_policy_params.append(prior_training_data[i][3])      
       
    #     prior_training_data_expect_rewards_mean = np.array(prior_training_data_expect_rewards_mean)
    #     prior_training_data_expect_rewards_sig = np.sqrt(np.array(prior_training_data_expect_rewards_sig)) # NOTE: add sqrt to get std from variance!!
    #     prior_training_data_policy_params = np.array(prior_training_data_policy_params)

    #     import pdb; pdb.set_trace()
    #     num_samples = len(prior_training_data)       
    #     samples_to_query, PI_o_all = [], []
    #     f_oStar = np.max(prior_training_data_expect_rewards_mean)
        
    #     # import pdb; pdb.set_trace()
    #     for i in range(0, num_samples):       
    #         mu_o = prior_training_data_expect_rewards_mean[i]
    #         sigma_o = prior_training_data_expect_rewards_sig[i]  
    #         PI_o = norm.cdf((mu_o - f_oStar - eps)/sigma_o)
    #         PI_o_all.append(PI_o)
        
    #     max_PI_o = np.max(PI_o_all)
    #     max_PI_outcome_idx = np.argmax(PI_o_all) 
    #     import pdb; pdb.set_trace()

    #     if max_PI_outcome_idx not in queried_samples_all:         
    #         uncertaint_thresh =  prior_training_data_expect_rewards_sig[max_PI_outcome_idx]/np.sqrt(beta)
    #         if uncertaint_thresh > lambda_thresh:
    #             samples_to_query.append(max_PI_outcome_idx)

    #     queried_outcomes_arr = prior_training_data_o[samples_to_query]  
    #     print('samples_to_query', samples_to_query)            
    #     import pdb; pdb.set_trace()
    #     return samples_to_query, queried_outcomes_arr
    
    # DEBUGGING ISSUE W/ SIGMA PTS NOT UPDATING!!!!!!
    def compute_EPD_for_each_sample_updated(self, GP_mean_rews_all_data_current_reward_model, GP_var_rews_all_data_current_reward_model, \
        current_epoch, num_samples_each_epoch, work_dir, num_training_epochs, optimizer, current_reward_model, likelihood, mll, \
            agent, pi_tilda_mean, pi_tilda_cov, pi_tilda_wts, prior_training_data, \
                queried_samples_all, GP_training_data_x_all, GP_training_data_y_all, beta, initial_wts, cut_type, S):
        
        if current_epoch > 0:
            self.kappa = 0.7

        prior_training_data_expect_rewards_mean, prior_training_data_policy_params, \
            prior_training_data_expect_rewards_sig = [], [], []
        
        prior_training_data_o = np.empty([0,self.num_reward_features])
        
        for i in range(len(prior_training_data)):
            prior_training_data_o = np.vstack((prior_training_data_o, prior_training_data[i][0]))
            prior_training_data_expect_rewards_mean.append(prior_training_data[i][1])
            prior_training_data_expect_rewards_sig.append(prior_training_data[i][2])
            prior_training_data_policy_params.append(prior_training_data[i][3])      
       
        prior_training_data_expect_rewards_mean = np.array(GP_mean_rews_all_data_current_reward_model) #OLD: np.array(prior_training_data_expect_rewards_mean)
        prior_training_data_expect_rewards_sig = np.array(np.sqrt(GP_var_rews_all_data_current_reward_model)) #OLD: np.sqrt(np.array(prior_training_data_expect_rewards_sig)) # NOTE: add sqrt to get std from variance!!
        prior_training_data_policy_params = np.array(prior_training_data_policy_params)

        print('TODO: need to update prior_training_data_expect_rewards_sig and prior_training_data_expect_rewards_mean when testing out new training set sizes!!!!!')
        import pdb; pdb.set_trace() 

        '''TODO: directly pass in prior_training_data_expect_rewards_mean, prior_training_data_expect_rewards_sig instead
        of getting these from prior_training_data
        
        prior_training_data_o: nx7 arr (7 reward features)
        prior_training_data_expect_rewards_mean: (n,) arr
        prior_training_data_expect_rewards_sig: (n,) arr
        prior_training_data_policy_params: nx8 arr
        '''
        num_samples = len(prior_training_data)       
        samples_to_query, KL_div_all, KL_div_all_wts = [], [], []
        
        # -----------------FOR DEBUGGING------------------------------
        #import pdb; pdb.set_trace()
        #n_GP_training_samples = 15
        #queried_samples_all = np.arange(n_GP_training_samples).tolist()
        #fp = 'gp_rewsVars_trainingSize_' + str(n_GP_training_samples) + '_sigVar_4.npy'
        #testdir = '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-HIL-ARL-exps/normal/potato/exp_2/GP_reward_model_data/2-11-21-GP-training-size-eval/'
        #prior_training_data_expect_rewards_mean = np.load(testdir+fp)[:,0]
        #prior_training_data_expect_rewards_sig = np.sqrt(np.load(testdir+fp)[:,1])
        
        diff_rews = []
        # import pdb; pdb.set_trace()
        #--------------------------------------------------------------

        # iterate through all samples in current epoch in training data set
        for i in range(0, num_samples):       
            # don't iterate through all samples, skip already queried and ones from previous rollouts (?)     
            if i in queried_samples_all: # total_samples - samples_in_current_epoch
                continue            
            else:
                outcome = np.expand_dims(prior_training_data_o[i,:],axis=0)
                mean_expect_reward = prior_training_data_expect_rewards_mean[i]
                sigma_expect_reward = prior_training_data_expect_rewards_sig[i]            

                sigma_pt_1 = mean_expect_reward + sigma_expect_reward
                sigma_pt_2 = mean_expect_reward - sigma_expect_reward
                sigma_pts = [sigma_pt_1, sigma_pt_2]

                # update w/ 1st sigma pt
                KL_div_sigma_pts = []
                for sigma_pt in sigma_pts:
                    outcomes_to_update = outcome
                    rewards_to_update = np.array([sigma_pt])
                    
                    #updating hypoth_reward_model for this sample instead of actual model           
                    hypoth_reward_model = copy.deepcopy(current_reward_model)
                    hypoth_likelihood = copy.deepcopy(likelihood)
                    hypoth_optimizer = copy.deepcopy(optimizer) #TODO: need to redefine this using hypoth_reward_model?
                    hypoth_mll = copy.deepcopy(mll)            
                    
                    # GP_training_data_x_all and GP_training_data_y_all are previous training data for 
                    og_train_x = copy.deepcopy(GP_training_data_x_all)
                    og_train_y = copy.deepcopy(GP_training_data_y_all)            
                    updated_train_x = np.vstack((og_train_x, outcomes_to_update))
                    updated_train_y = np.concatenate((og_train_y, rewards_to_update))  
                    
                    #update hypoth reward model with this outcome
                    #-------------original
                    continue_training = False
                    hypoth_reward_model = self.update_reward_GPmodel(work_dir, continue_training, num_training_epochs, hypoth_optimizer, hypoth_reward_model, \
                        hypoth_likelihood, hypoth_mll, updated_train_x, updated_train_y)
                    # ---------------------                           
            
                    #calculate rewards for training data under updated reward model                 
                    mean_exp_rewards, var_exp_rewards = self.calc_expected_reward_for_observed_outcome_w_GPmodel(hypoth_reward_model, \
                        hypoth_likelihood, prior_training_data_o)
                    #import pdb; pdb.set_trace()

                    print('diff rews', (np.abs(prior_training_data_expect_rewards_mean-mean_exp_rewards)))
                    print('sum diff rews', np.sum((np.abs(prior_training_data_expect_rewards_mean-mean_exp_rewards))))
                    
                    #Calculate policy update under updated reward model                              
                    # SCALED - TODO: clean this up!!!!!!!!!!!!!!
                    prior_training_data_policy_params_scaled = agent.scale_pol_params(prior_training_data_policy_params)
                    pi_star_mean_scaled, pi_star_cov_scaled, reps_wts_scaled = agent.update_policy_REPS(mean_exp_rewards, \
                        prior_training_data_policy_params_scaled, rel_entropy_bound = 1.5, min_temperature=0.001) #rel_entropy_bound = 0.4
                    
                    if self.scale_pol_params:
                        pi_star_mean = pi_star_mean_scaled 
                        pi_star_cov = pi_star_cov_scaled
                    else:
                        # UNSCALED
                        pi_star_mean, pi_star_cov, reps_wts = agent.update_policy_REPS(mean_exp_rewards, \
                            prior_training_data_policy_params, rel_entropy_bound = 1.5, min_temperature=0.001) #rel_entropy_bound = 0.4

                    pi_star_wts = agent.calculate_REPS_wts(mean_exp_rewards, rel_entropy_bound = 1.5, min_temperature=0.001)

                    print('pi_tilda_mean (new policy under current reward model)' , pi_tilda_mean)
                    print('pi_star_mean (new policy under updated reward model)' , pi_star_mean)
                    # import pdb; pdb.set_trace()

                    if self.sampl_or_weight_kld_calc == 'sampling':
                        ######### KL DIV SAMPLING
                        print('computing KL div')
                        n_samples = 5000 # 1000 # 10000 #20 #10000 #20
                        KL_div = self.compute_KL_div_sampling_updated(agent, n_samples, pi_tilda_mean, pi_tilda_cov, \
                            pi_star_mean, pi_star_cov, initial_wts, cut_type, S)
                        print('KLdiv_sampling', KL_div)     

                    elif self.sampl_or_weight_kld_calc == 'weight':          
                        # ############ KL DIV WEIGHTS SPACE
                        KL_div = self.compute_kl_divergence_wts(pi_star_wts, pi_tilda_wts)   
                    
                    KL_div_sigma_pts.append(KL_div)                
                print('KL div both sigma pts:', KL_div_sigma_pts,', mean_KL:  ', np.mean(KL_div_sigma_pts))
                KL_div = np.mean(KL_div_sigma_pts)

                # save to buffer
                KL_div_all.append(KL_div) 
                # determine whether to query by checking threshold
                if (np.all(np.isnan(KL_div)==True))==False and np.any(KL_div >= self.kappa):
                    samples_to_query.append(i)

        #Check if we've already queried these samples. If yes, remove from list:
        # import pdb; pdb.set_trace()
        print('KL divs', KL_div_all)        
        print('median KL DIV', np.median(KL_div_all))
        print('mean KL DIV', np.mean(KL_div_all))
        samples_to_query_new = self.remove_already_queried_samples_from_list(samples_to_query, queried_samples_all)
        print('new samples_to_query', samples_to_query_new)
        print('num new samples to query', len(samples_to_query_new))
        plt.hist(KL_div_all)
        if self.sampl_or_weight_kld_calc == 'sampling':
            plt.title('histogram of KLD values calculated w/ sampling - %i pol param samples'%n_samples)
        elif self.sampl_or_weight_kld_calc == 'weight':
            plt.title('histogram of KLD values calculated in weight space - initial GP training samples n = %i'%self.n_GP_training_samples)
        plt.xlabel('KLD values')
        plt.ylabel('freq')
        plt.show()
        import pdb; pdb.set_trace()
        queried_outcomes_arr = prior_training_data_o[samples_to_query_new]              
        import pdb; pdb.set_trace()
        return samples_to_query_new, queried_outcomes_arr #indexes of samples to query from expert

    # ORIGINAL FUNCTION
    # def compute_EPD_for_each_sample_updated(self, current_epoch, num_samples_each_epoch, work_dir, num_training_epochs, optimizer, current_reward_model, likelihood, mll, \
    #         agent, pi_tilda_mean, pi_tilda_cov, pi_tilda_wts, pi_current_mean, pi_current_cov, prior_training_data, \
    #             queried_samples_all, GP_training_data_x_all, GP_training_data_y_all, beta, initial_wts, cut_type, S):

    #     prior_training_data_expect_rewards_mean, prior_training_data_policy_params, \
    #         prior_training_data_expect_rewards_sig = [], [], []
        
    #     prior_training_data_o = np.empty([0,self.num_reward_features])
        
    #     for i in range(len(prior_training_data)):
    #         prior_training_data_o = np.vstack((prior_training_data_o, prior_training_data[i][0]))
    #         prior_training_data_expect_rewards_mean.append(prior_training_data[i][1])
    #         prior_training_data_expect_rewards_sig.append(prior_training_data[i][2])
    #         prior_training_data_policy_params.append(prior_training_data[i][3])      
       
    #     prior_training_data_expect_rewards_mean = np.array(prior_training_data_expect_rewards_mean)
    #     prior_training_data_expect_rewards_sig = np.sqrt(np.array(prior_training_data_expect_rewards_sig)) # NOTE: add sqrt to get std from variance!!
    #     prior_training_data_policy_params = np.array(prior_training_data_policy_params)

    #     print('TODO: need to update prior_training_data_expect_rewards_sig and prior_training_data_expect_rewards_mean when testing out new training set sizes!!!!!')
    #     import pdb; pdb.set_trace() 
    #     '''
    #     prior_training_data_o: nx7 arr (7 reward features)
    #     prior_training_data_expect_rewards_mean: (n,) arr
    #     prior_training_data_expect_rewards_sig: (n,) arr
    #     prior_training_data_policy_params: nx8 arr
    #     '''

    #     num_samples = len(prior_training_data)       
    #     samples_to_query, KL_div_all, KL_div_all_wts = [], [], []
        
    #     # -----------------FOR DEBUGGING------------------------------
    #     #import pdb; pdb.set_trace()
    #     queried_samples_all = np.arange(5).tolist()
    #     fp = 'gp_rewsVars_trainingSize_5_sigVar_4.npy'
    #     testdir = '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-HIL-ARL-exps/normal/potato/exp_2/GP_reward_model_data/2-11-21-GP-training-size-eval/'
    #     prior_training_data_expect_rewards_mean = np.load(testdir+fp)[:,0]
    #     prior_training_data_expect_rewards_sig = np.sqrt(np.load(testdir+fp)[:,1])
    #     diff_rews = []
    #     # import pdb; pdb.set_trace()
    #     #--------------------------------------------------------------

    #     # iterate through all samples in current epoch in training data set
    #     for i in range(0, num_samples):       
    #         # don't iterate through all samples, skip already queried and ones from previous rollouts (?)     
    #         if i in queried_samples_all: # total_samples - samples_in_current_epoch
    #             continue            
    #         else:
    #             outcome = np.expand_dims(prior_training_data_o[i,:],axis=0)
    #             mean_expect_reward = prior_training_data_expect_rewards_mean[i]
    #             sigma_expect_reward = prior_training_data_expect_rewards_sig[i]            

    #             sigma_pt_1 = mean_expect_reward + sigma_expect_reward
    #             sigma_pt_2 = mean_expect_reward - sigma_expect_reward

    #             #### SHOULD be using sigma points to estimate UPDATED reward model!
    #             # TODO: should be updating reward model separately for each sigma pt??
    #             import pdb; pdb.set_trace()
    #             #outcomes_to_update = np.vstack((outcome, outcome))
    #             #rewards_to_update = np.array([sigma_pt_1, sigma_pt_2])
    #             # update w/ 1st sigma pt
    #             outcomes_to_update = outcome
    #             rewards_to_update = np.array([sigma_pt_1])
                
    #             #updating hypoth_reward_model for this sample instead of actual model           
    #             hypoth_reward_model = copy.deepcopy(current_reward_model)
    #             hypoth_likelihood = copy.deepcopy(likelihood)
    #             hypoth_optimizer = copy.deepcopy(optimizer) #TODO: need to redefine this using hypoth_reward_model?
    #             hypoth_mll = copy.deepcopy(mll)            
                
    #             # GP_training_data_x_all and GP_training_data_y_all are previous training data for 
    #             og_train_x = copy.deepcopy(GP_training_data_x_all)
    #             og_train_y = copy.deepcopy(GP_training_data_y_all)            
    #             updated_train_x = np.vstack((og_train_x, outcomes_to_update))
    #             updated_train_y = np.concatenate((og_train_y, rewards_to_update))  
    #             import pdb; pdb.set_trace()          
                
    #             # NOTE: MIGHT need to update likelihood here b/c of added noise params 
    #             #hypoth_likelihood = gpytorch.likelihoods.FixedNoiseGaussianLikelihood(torch.ones(updated_train_x.shape[0]) * beta)

    #             #update hypoth reward model with this outcome
    #             #-------------original
    #             continue_training = False
    #             hypoth_reward_model = self.update_reward_GPmodel(work_dir, continue_training, num_training_epochs, hypoth_optimizer, hypoth_reward_model, \
    #                 hypoth_likelihood, hypoth_mll, updated_train_x, updated_train_y)
    #             # ---------------------

    #             # # ----------------------------------------------DEBUGGGGGGGGGGGGg 1 
    #             # outcomes_to_update = outcome
    #             # rewards_to_update = np.array([sigma_pt_2])                
    #             # #updating hypoth_reward_model for this sample instead of actual model                   
    #             # # GP_training_data_x_all and GP_training_data_y_all are previous training data for                           
    #             # updated_train_x = np.vstack((updated_train_x, outcomes_to_update))
    #             # updated_train_y = np.concatenate((updated_train_y, rewards_to_update))    

    #             # continue_training = False
    #             # hypoth_reward_model = self.update_reward_GPmodel(work_dir, continue_training, num_training_epochs, hypoth_optimizer, hypoth_reward_model, \
    #             #     hypoth_likelihood, hypoth_mll, updated_train_x, updated_train_y)
    #             # import pdb; pdb.set_trace()
    #             #-----------------------------------------------------------                 
        
    #             import pdb; pdb.set_trace()
    #             #calculate rewards for training data under updated reward model                 
    #             mean_exp_rewards, var_exp_rewards = self.calc_expected_reward_for_observed_outcome_w_GPmodel(hypoth_reward_model, \
    #                 hypoth_likelihood, prior_training_data_o)
    #             import pdb; pdb.set_trace()

    #             print('diff rews', (np.abs(prior_training_data_expect_rewards_mean-mean_exp_rewards)))
    #             import pdb; pdb.set_trace()
    #             #Calculate policy update under updated reward model            
    #             # NOTE: 2/4/21 update: lower rel_entropy_bound so new policy cov doesn't deviate too far 
                
    #             # SCALED - TODO: clean this up!!!!!!!!!!!!!!
    #             prior_training_data_policy_params_scaled = agent.scale_pol_params(prior_training_data_policy_params)
    #             pi_star_mean_scaled, pi_star_cov_scaled, reps_wts_scaled = agent.update_policy_REPS(mean_exp_rewards, \
    #                 prior_training_data_policy_params_scaled, rel_entropy_bound = 1.5, min_temperature=0.001) #rel_entropy_bound = 0.4
                
    #             if self.scale_pol_params:
    #                 #pi_star_wts = reps_wts_scaled
    #                 pi_star_mean = pi_star_mean_scaled 
    #                 pi_star_cov = pi_star_cov_scaled
    #             else:
    #                 # UNSCALED
    #                 pi_star_mean, pi_star_cov, reps_wts = agent.update_policy_REPS(mean_exp_rewards, \
    #                     prior_training_data_policy_params, rel_entropy_bound = 1.5, min_temperature=0.001) #rel_entropy_bound = 0.4
    #                 #pi_star_wts = reps_wts

    #             pi_star_wts = agent.calculate_REPS_wts(mean_exp_rewards, rel_entropy_bound = 1.5, min_temperature=0.001)

    #             print('pi_current_mean (policy before updating)' , pi_current_mean)
    #             print('pi_tilda_mean (new policy under current reward model)' , pi_tilda_mean)
    #             print('pi_star_mean (new policy under updated reward model)' , pi_star_mean)
    #             # import pdb; pdb.set_trace()

    #             # save policy mean and covs for debugging
    #             # np.savez(work_dir + '/' + 'GP_reward_model_data/policy_pi_star_tilda_data/' + 'epoch_' + str(current_epoch) + '_pi_star_tilda_sample_' + str(i) + '.npz', 
    #             #     pi_current_mean = pi_current_mean, pi_tilda_mean = pi_tilda_mean, pi_star_mean = pi_star_mean,
    #             #         pi_current_cov = pi_current_cov, pi_tilda_cov = pi_tilda_cov, pi_star_cov = pi_star_cov)
    #             # import pdb; pdb.set_trace()

    #             # note - 40 is higher # samples (used to be 10)
    #             ######### KL DIV ANALYTICAL
    #             #print('computing KL div analytical')
    #             # import pdb; pdb.set_trace()
    #             #KL_div = self.compute_kl_divergence(pi_tilda_mean, pi_tilda_cov, pi_star_mean, pi_star_cov)[0][0]
    #             #print('KLdiv_analytical', KL_div)

    #             if self.sampl_or_weight_kld_calc == 'sampling':
    #                 ######### KL DIV SAMPLING
    #                 print('computing KL div')
    #                 n_samples = 5000 # 1000 # 10000 #20 #10000 #20
    #                 KL_div = self.compute_KL_div_sampling_updated(agent, n_samples, pi_tilda_mean, pi_tilda_cov, \
    #                     pi_star_mean, pi_star_cov, pi_current_mean, pi_current_cov, initial_wts, cut_type, S)
    #                 print('KLdiv_sampling', KL_div)     

    #             elif self.sampl_or_weight_kld_calc == 'weight':          
    #                 # ############ KL DIV WEIGHTS SPACE
    #                 KL_div = self.compute_kl_divergence_wts(pi_star_wts, pi_tilda_wts)   
    #                 #np.savetxt('/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-HIL-ARL-exps/scoring/tomato/exp_1/GP_reward_model_data/KLD_debug_new/2-10-21/pi_star_rews_updated_reward_model_sample' + str(i) +'.txt', mean_exp_rewards)
    #                 #np.savetxt('/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-HIL-ARL-exps/scoring/tomato/exp_1/GP_reward_model_data/KLD_debug_new/2-10-21/pi_tilda_pi_star_wts_sample' + str(i) +'.txt', \
    #                     #np.concatenate((np.expand_dims(pi_tilda_wts,axis=1),np.expand_dims(pi_star_wts, axis=1)),axis=1))
    #                 print('KLdiv_weights', KL_div)

    #             # save to buffer
    #             KL_div_all.append(KL_div)   

    #             # determine whether to query by checking threshold
    #             if (np.all(np.isnan(KL_div)==True))==False and np.any(KL_div >= self.kappa):
    #                 samples_to_query.append(i)

    #     #Check if we've already queried these samples. If yes, remove from list:
    #     # import pdb; pdb.set_trace()
    #     print('KL divs', KL_div_all)        
    #     print('median KL DIV', np.median(KL_div_all))
    #     print('mean KL DIV', np.mean(KL_div_all))
    #     samples_to_query_new = self.remove_already_queried_samples_from_list(samples_to_query, queried_samples_all)
    #     print('new samples_to_query', samples_to_query_new)
    #     print('num new samples to query', len(samples_to_query_new))
    #     plt.hist(KL_div_all)
    #     if self.sampl_or_weight_kld_calc == 'sampling':
    #         plt.title('histogram of KLD values calculated w/ sampling - %i pol param samples'%n_samples)
    #     elif self.sampl_or_weight_kld_calc == 'weight':
    #         plt.title('histogram of KLD values calculated in weight space')
    #     plt.xlabel('KLD values')
    #     plt.ylabel('freq')
    #     plt.show()
    #     queried_outcomes_arr = prior_training_data_o[samples_to_query_new]              
    #     import pdb; pdb.set_trace()
    #     return samples_to_query_new, queried_outcomes_arr #indexes of samples to query from expert
    
    def update_reward_GPmodel(self, work_dir, continue_training, num_training_epochs, optimizer, model, likelihood, mll, updated_train_x, updated_train_y):
        # if updated_train data are np arrays, convert to torch float tensors
        #import pdb; pdb.set_trace()
        if type(updated_train_x)==np.ndarray:
            updated_train_x = torch.from_numpy(updated_train_x)
            updated_train_x = updated_train_x.float()

        if type(updated_train_y)==np.ndarray:
            updated_train_y = torch.from_numpy(updated_train_y)
            updated_train_y = updated_train_y.float()
        
        model.set_train_data(inputs = updated_train_x, targets = updated_train_y, strict = False)

        epochs_to_cont_training = num_training_epochs        
        if epochs_to_cont_training != 0:
            model = self.train_GPmodel(work_dir, epochs_to_cont_training, optimizer, model, likelihood, mll, updated_train_x, updated_train_y)
        
        return model
    
    def calc_mean_std_reward_features(self, cut_type, save_mean_std = False):
        '''
        save_mean_std: True, False
        cut_type: normal, pivchop, scoring

        this function calculates the mean and std from prior training data and saves to an array for loading in the future
        '''
        base_dir = '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/' + cut_type + '/'
        food_types = ['potato', 'celery', 'carrot', 'banana', 'tomato', 'mozz']
        reward_feats_all_foods = np.empty((0,7))
        for food in food_types:
            #import pdb; pdb.set_trace()
            work_dir = base_dir + food + '/'
            exp_folder = os.listdir(work_dir)
            work_dir = work_dir + exp_folder[0] + '/'

            reward_feats = np.load(work_dir + '/reward_features_all_samples.npy')
            # import pdb; pdb.set_trace()
            if len(np.where(reward_feats==np.inf)[0])!= 0: # there are inf's in array
                inf_inds = np.unique(np.where(reward_feats==np.inf)[0])
                last_inf_ind = inf_inds.max()
                reward_feats = reward_feats[last_inf_ind+1:]
            reward_feats_all_foods = np.vstack((reward_feats_all_foods, reward_feats))
        
        #import pdb; pdb.set_trace()
        reward_feats_mean = np.mean(reward_feats_all_foods, axis=0)
        reward_feats_std = np.std(reward_feats_all_foods, axis=0)

        if save_mean_std:
            np.save(base_dir + '/' + cut_type + '_reward_feats_mean_std' + '.npy', np.array([reward_feats_mean, reward_feats_std]))
        
        return reward_feats_mean, reward_feats_std

    def standardize_reward_feature(self, cut_type, current_reward_feat):
        '''
        standardize reward features using mean and std from previous training data
        '''
        base_dir = '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/' + cut_type + '/'
        mean_std_reward_feats = np.load(base_dir + '/' + cut_type + '_reward_feats_mean_std' + '.npy')
        mean_reward_feats = mean_std_reward_feats[0,:]
        std_reward_feats = mean_std_reward_feats[1,:]
        #import pdb; pdb.set_trace()
        standardized_reward_feat = (current_reward_feat - mean_reward_feats)/std_reward_feats

        return standardized_reward_feat

    def unstandardize_reward_feature(self, cut_type, standardized_reward_feat):
        base_dir = '/home/sony/Documents/cutting_RL_experiments/data/Jan-2021-LL-param-exps/' + cut_type + '/'
        mean_std_reward_feats = np.load(base_dir + '/' + cut_type + '_reward_feats_mean_std' + '.npy')
        mean_reward_feats = mean_std_reward_feats[0,:]
        std_reward_feats = mean_std_reward_feats[1,:]

        unstandardized_reward_feat = (standardized_reward_feat*std_reward_feats) + mean_reward_feats

        return unstandardized_reward_feat
    
    def compute_kl_divergence(self, pm, pv, qm, qv):    
        """
        Kullback-Liebler divergence analytical
        """        
        n_dims = pv.shape[0]

        #qv = qv + np.eye(n_dims)*0.5
        #pv = pv + np.eye(n_dims)*0.5
        # import pdb; pdb.set_trace()
        det_p = np.linalg.det(pv)
        det_q = np.linalg.det(qv)
        inv_p = np.linalg.pinv(pv)
        inv_q = np.linalg.pinv(qv)
        #inv_p = np.linalg.inv(pv)
        #inv_q = np.linalg.inv(qv)

        log_det1_det2 = np.log(det_q) - np.log(det_p)
        trace_pq = np.trace(inv_q*pv)

        mu2_minus_mu1 = np.array([qm-pm]).T

        kl_div = 0.5*(log_det1_det2 - n_dims + trace_pq +  np.matmul(np.matmul(mu2_minus_mu1.T,inv_q),mu2_minus_mu1))

        # import pdb; pdb.set_trace()
        return kl_div
    
    def compute_kl_divergence_wts(self, pi_star_wts, pi_tilda_wts):
        num_samples = pi_star_wts.shape[0]
        kl_div = np.sum(pi_star_wts*np.log(pi_star_wts/pi_tilda_wts))
        # import pdb; pdb.set_trace()
        return kl_div
  

    def plot_kernel_length_scale(self,epoch,gpr_reward_model):
        #print('kernel length scale', gpr_reward_model.kernel_.get_params()['length_scale'])
        length_scale = gpr_reward_model.kernel_.get_params()['k2__length_scale']
        signal_var = gpr_reward_model.kernel_.get_params()['k1__constant_value']
        print('kernel length scale', length_scale)
        print('kernel signal variance', signal_var)

        #plt.figure()c
        plt.scatter(epoch, length_scale, color='green')
        #plt.title('kernel length scale vs epochs')
        #plt.xlabel('num epochs')
        #plt.ylabel('length scale')
        #plt.axis([0, 21, 0, 150])
        plt.pause(0.05)

    def plot_rewards_all_episodes(self,training_data_list, kappa):
        plt.plot(np.array(training_data_list)[:,1])
        plt.plot(np.array(training_data_list)[:,3])
        plt.xlabel('total episodes')
        plt.ylabel('rewards')
        plt.title('rewards vs. episodes, kappa = %f'%kappa)
        plt.legend(('mean_expected_reward from reward learner model', 'expert reward'))
        plt.show()

    def plot_mean_rewards_each_epoch(self, epoch,mean_reward_model_rewards_all_epochs,mean_expert_rewards_all_epochs,kappa):
        plt.plot(np.arange(epoch), mean_reward_model_rewards_all_epochs)
        plt.plot(np.arange(epoch), mean_expert_rewards_all_epochs)
        plt.xlabel('epochs')
        plt.ylabel('rewards')
        plt.title('rewards vs. epochs, kappa = %f'%kappa)
        plt.legend(('mean_expected_reward from reward learner model', 'mean expert reward'))
        plt.show()

    def plot_cumulative_queried_samples_vs_epochs(self, epoch,total_queried_samples_each_epoch,kappa):
        plt.plot(np.arange(epoch), total_queried_samples_each_epoch)
        plt.xlabel('epochs')
        plt.ylabel('total (cumululative) queried samples')
        plt.title('total (cumulative) queried samples vs. epochs, kappa = %f'%kappa)
        plt.show()