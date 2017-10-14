# Semantic Segmentation
### Summary
I trained a Fully Convolutional Network as described in [Long and Shelhamer's paper](https://people.eecs.berkeley.edu/~jonlong/long_shelhamer_fcn.pdf) to distinguish between road and non-road.

### Final Hyperparameters
 - Epochs: 16
 - Batch size: 1
 - Dropout probability: 0.2
 - Learning rate: 0.001
 - L2 regularization scale: 1e-3
 - stddev for truncated_normal_initializer: 0.01

### Experimentation
 - I tried a batch size of 5, but the model results were poor after 5 epochs
 - My dropout probability was originally 0.5, but the model had better results with 0.2
 - The L2 regularization and truncated_normal_initializer also improved my model results

### Example results
 ![Simple road](img/um_000022.png)
 ![Road with many cars](img/um_000061.png)
 ![Road with cars and motorcycle](img/umm_000024.png)

# Project Description

### Introduction
In this project, you'll label the pixels of a road in images using a Fully Convolutional Network (FCN).

### Setup
##### Frameworks and Packages
Make sure you have the following is installed:
 - [Python 3](https://www.python.org/)
 - [TensorFlow](https://www.tensorflow.org/)
 - [NumPy](http://www.numpy.org/)
 - [SciPy](https://www.scipy.org/)
##### Dataset
Download the [Kitti Road dataset](http://www.cvlibs.net/datasets/kitti/eval_road.php) from [here](http://www.cvlibs.net/download.php?file=data_road.zip).  Extract the dataset in the `data` folder.  This will create the folder `data_road` with all the training a test images.

### Start
##### Implement
Implement the code in the `main.py` module indicated by the "TODO" comments.
The comments indicated with "OPTIONAL" tag are not required to complete.
##### Run
Run the following command to run the project:
```
python main.py
```
**Note** If running this in Jupyter Notebook system messages, such as those regarding test status, may appear in the terminal rather than the notebook.

### Submission
1. Ensure you've passed all the unit tests.
2. Ensure you pass all points on [the rubric](https://review.udacity.com/#!/rubrics/989/view).
3. Submit the following in a zip file.
 - `helper.py`
 - `main.py`
 - `project_tests.py`
 - Newest inference images from `runs` folder  (**all images from the most recent run**)
 
 ## How to write a README
A well written README file can enhance your project and portfolio.  Develop your abilities to create professional README files by completing [this free course](https://www.udacity.com/course/writing-readmes--ud777).
