import os

import numpy as np

import torch
import torch.optim as optim


class NnetHelper():

	def __init__(self, num_epoch=10, batch_size=64):
		self.num_epoch = num_epoch
		self.batch_size = batch_size


	def train_network(self, nnet, train_examples):

		train_examples = [ex for itr in train_examples for episode in itr for ex in episode]
		np.random.shuffle(train_examples)

		optimizer = optim.Adam(nnet.parameters())

		for _ in range(self.num_epoch):
			for i in range(0, len(train_examples), self.batch_size):

				states, pis, rewards = self.handle_data(train_examples[i:i+self.batch_size])

				pred_pi, pred_v = nnet(states)

				loss_v, loss_pi = self.loss_function(pred_v=pred_v, z=rewards, pi=pis, pred_pi=pred_pi)
				total_loss = loss_pi + loss_v

				optimizer.zero_grad()
				total_loss.backward()
				optimizer.step()

			print('training loss: {:.3f} --- {:.3f}'.format(loss_pi.data.numpy(), loss_v.data.numpy()))

		return nnet


	def handle_data(self, batch_examples):
		
		states, pis, rewards = zip(*batch_examples)
		
		states = torch.FloatTensor(np.array(states).astype(np.float64))
		states = states.view(states.size(0), 1, states.size(1), states.size(2))
		pis = torch.FloatTensor(np.array(pis))
		rewards = torch.FloatTensor(np.array(rewards).astype(np.float64))
		
		return states, pis, rewards


	def loss_function(self, pred_v=None, z=None, pred_pi=None, pi=None):
		v_loss = torch.sum((z - pred_v.view(-1))**2) / z.size(0)
		pi_loss = torch.sum(pi*torch.log(pred_pi + 1e-8)) / pi.size(0)
		return v_loss, -pi_loss


	def save_network(self, nnet, folder=None, filename=None):
		filepath = os.path.join(folder, filename)
		torch.save(nnet.state_dict(), filepath)


	def load_network(self, nnet, folder=None, filename=None):
		filepath = os.path.join(folder, filename)
		cp = torch.load(filepath)
		nnet.load_state_dict(torch.load(filepath))
