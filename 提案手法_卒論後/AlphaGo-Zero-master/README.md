# AlphaGo-Zero

This repository contains an implementation of DeepMind's AlphaGo Zero alogrithm. The algorithm was tested out on X's and O's as well as Connect 3 and Connect 4. (Games with a much lower number of potential states than Go). 


## Overview
AlphaGo zero combines a Monte Carlo Tree Search with a Deep Neural Network to learn entirely through self-play, with no need for human intervention beyond encoding the rules of the game. Details for the inspiration come from DeepMind's original paper which can be found [here](https://deepmind.com/documents/119/agz_unformatted_nature.pdf). Additionally [this tutorial](https://web.stanford.edu/~surag/posts/alphazero.html) was very helpful and [this website](http://mcts.ai/) is a great resource for Monte Carlo Tree Search material.

If you want to test out this project for yourself:

* `Main.py` is the script that trains the network and saves them in the `models` folder.
* `showdown.py`allows you to play against a trained network, or see two networks face off against eachother.

## Results
Three different games were tested out. All were trained on a single (slow) CPU.

* **X's and O's**: The game is solved after about 5 iterations and will end in a draw every time (against itself or a human player).
* **Connect 3**: This was a game I made up myself to test scaling the network up to Connect4. It turns out it's a game with which the first player will always win (and the network will figure this out after about 5 iterations).
* **Connect 4**: On a 6x7 board my CPU didn't converge after leaving it running over night. After 10 iterations it does reasonably well, it beats me about 25-33% of the time (though that's not saying much).

## Files
* `Main.py` - Takes input arguments and uses the `solver` class to train the network.
* `Solver.py`- Class with all necessary method to perform policy iteration.
* `nnetHelper.py` - Helper class for training/saving/loading the neural network.
* `mcts.py` - Monte Carlo Tree Search class.
* `model.py` - ConvNet classes. Each game has it's own network.
* `xandos.py`/`connect4.py` - Classes for each game.
* `showdown.py` - play games with human/AlphaGo

## Requirements
Pytorch >= 0.4

NumPy
