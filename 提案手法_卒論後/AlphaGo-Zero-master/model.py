import torch
import torch.nn as nn
import torch.nn.functional as F


class C4Net_6x7(nn.Module):

	def __init__(self, num_inputs=None, num_actions=None):
		super(C4Net_6x7, self).__init__()

		self.main = nn.Sequential()

		self.main.add_module('Conv_1', nn.Conv2d(1, 64, 3, stride=1, padding=1))
		self.main.add_module('bn_1', nn.BatchNorm2d(64))
		self.main.add_module('relu_1', nn.ReLU())

		self.main.add_module('Conv_2', nn.Conv2d(64, 128, 3, stride=1, padding=1))
		self.main.add_module('bn_2', nn.BatchNorm2d(128))
		self.main.add_module('relu_2', nn.ReLU())

		self.main.add_module('Conv_3', nn.Conv2d(128, 256, 3, stride=1, padding=1))
		self.main.add_module('bn_3', nn.BatchNorm2d(256))
		self.main.add_module('relu_3', nn.ReLU())

		self.main.add_module('Conv_4', nn.Conv2d(256, 512, 3, stride=1))
		self.main.add_module('bn_4', nn.BatchNorm2d(512))
		self.main.add_module('relu_4', nn.ReLU())

		self.main.add_module('Conv_5', nn.Conv2d(512, 512, (2, 3), stride=1))
		self.main.add_module('bn_5', nn.BatchNorm2d(512))
		self.main.add_module('relu_5', nn.ReLU())

		self.main.add_module('Conv_6', nn.Conv2d(512, 512, 3, stride=1))
		self.main.add_module('relu_6', nn.ReLU())

		self.fc1 = nn.Linear(512, 256)
		self.policy_output = nn.Linear(256, num_actions)
		self.value_output = nn.Linear(256, 1)


	def forward(self, inputs):

		x = inputs
		x = self.main(x)
		
		x = x.view(-1, 512)
		x = F.dropout(F.relu(self.fc1(x)), p=0.3, training=self.training)

		return F.softmax(self.policy_output(x), dim=1), F.tanh(self.value_output(x))

class C4Net_5x5(nn.Module):

	def __init__(self, num_inputs=None, num_actions=None):
		super(C4Net_5x5, self).__init__()

		self.main = nn.Sequential()

		self.main.add_module('Conv_1', nn.Conv2d(1, 64, 3, stride=1, padding=1))
		self.main.add_module('bn_1', nn.BatchNorm2d(64))
		self.main.add_module('relu_1', nn.ReLU())

		self.main.add_module('Conv_2', nn.Conv2d(64, 128, 3, stride=1, padding=1))
		self.main.add_module('bn_2', nn.BatchNorm2d(128))
		self.main.add_module('relu_2', nn.ReLU())

		self.main.add_module('Conv_3', nn.Conv2d(128, 256, 3, stride=1, padding=1))
		self.main.add_module('bn_3', nn.BatchNorm2d(256))
		self.main.add_module('relu_3', nn.ReLU())

		self.main.add_module('Conv_4', nn.Conv2d(256, 512, 3, stride=1))
		self.main.add_module('bn_4', nn.BatchNorm2d(512))
		self.main.add_module('relu_4', nn.ReLU())

		self.main.add_module('Conv_5', nn.Conv2d(512, 512, 3, stride=1))
		self.main.add_module('relu_5', nn.ReLU())

		self.fc1 = nn.Linear(512, 256)
		self.policy_output = nn.Linear(256, num_actions)
		self.value_output = nn.Linear(256, 1)


	def forward(self, inputs):

		x = inputs
		x = self.main(x)
		
		x = x.view(-1, 512)
		x = F.dropout(F.relu(self.fc1(x)), p=0.3, training=self.training)

		return F.softmax(self.policy_output(x), dim=1), F.tanh(self.value_output(x))


class XandosNet(nn.Module):

	def __init__(self, num_inputs=None, num_actions=9):
		super(XandosNet, self).__init__()

		self.main = nn.Sequential()

		self.main.add_module('Conv_1', nn.Conv2d(1, 64, 3, stride=1, padding=1))
		self.main.add_module('bn_1', nn.BatchNorm2d(64))
		self.main.add_module('relu_1', nn.ReLU())

		self.main.add_module('Conv_2', nn.Conv2d(64, 128, 3, stride=1, padding=1))
		self.main.add_module('bn_2', nn.BatchNorm2d(128))
		self.main.add_module('relu_2', nn.ReLU())

		self.main.add_module('Conv_3', nn.Conv2d(128, 256, 3, stride=1, padding=1))
		self.main.add_module('bn_3', nn.BatchNorm2d(256))
		self.main.add_module('relu_3', nn.ReLU())

		self.main.add_module('Conv_4', nn.Conv2d(256, 512, 3, stride=1))
		self.main.add_module('relu_4', nn.ReLU())

		self.fc1 = nn.Linear(512, 256)
		self.policy_output = nn.Linear(256, num_actions)
		self.value_output = nn.Linear(256, 1)


	def forward(self, inputs):

		x = inputs
		x = self.main(x)
		
		x = x.view(-1, 512)
		x = F.dropout(F.relu(self.fc1(x)), p=0.3, training=self.training)

		return F.softmax(self.policy_output(x), dim=1), F.tanh(self.value_output(x))

# ========== ぷよぷよ用ニューラルネットワーク ==========

class PuyoNet(nn. Module):
    """
    ぷよぷよ用のニューラルネットワーク
    入力: (batch, 1, 14, 6) の盤面
    出力: (policy, value)
      - policy: (batch, 24) 各行動の確率
      - value:  (batch, 1) 局面評価 [-1, 1]
    """
    def __init__(self, board_height=14, board_width=6, num_actions=24):
        super(PuyoNet, self).__init__()
        
        self.board_height = board_height
        self.board_width = board_width
        self.num_actions = num_actions
        
        # 畳み込み層（Connect4のネットワークを参考）
        self.main = nn.Sequential()
        
        self.main.add_module('Conv_1', nn.Conv2d(1, 64, 3, stride=1, padding=1))
        self.main.add_module('bn_1', nn.BatchNorm2d(64))
        self.main.add_module('relu_1', nn.ReLU())
        
        self.main.add_module('Conv_2', nn.Conv2d(64, 128, 3, stride=1, padding=1))
        self.main.add_module('bn_2', nn.BatchNorm2d(128))
        self.main.add_module('relu_2', nn.ReLU())
        
        self.main.add_module('Conv_3', nn.Conv2d(128, 128, 3, stride=1, padding=1))
        self.main.add_module('bn_3', nn.BatchNorm2d(128))
        self.main.add_module('relu_3', nn.ReLU())
        
        # 全結合層
        fc_input_size = 128 * board_height * board_width
        self.fc1 = nn.Linear(fc_input_size, 256)
        
        # Policy Head（行動確率）
        self.policy_output = nn.Linear(256, num_actions)
        
        # Value Head（局面評価）
        self.value_output = nn.Linear(256, 1)
    
    def forward(self, inputs):
        """
        順伝播
        
        引数:
            inputs: (batch, 1, 14, 6) の盤面テンソル
        
        返り値:
            policy: (batch, 24) 行動確率分布
            value: (batch, 1) 局面評価値
        """
        x = inputs
        x = self.main(x)
        
        # 平坦化
        x = x. view(-1, 128 * self. board_height * self.board_width)
        x = F.dropout(F.relu(self.fc1(x)), p=0.3, training=self.training)
        
        # Policy出力
        policy = F.softmax(self.policy_output(x), dim=1)
        
        # Value出力
        value = torch.tanh(self.value_output(x))
        
        return policy, value
