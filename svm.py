from pprint import pprint
from time import time
import logging
import numpy as np 
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedKFold
from preprocess import preprocessor
from util import load_pickle, save_pickle, make_dir
from sklearn.model_selection import learning_curve, validation_curve,\
			cross_val_score, GridSearchCV
import matplotlib.pyplot as plt  
import json

############################# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

if __name__ == '__main__':	
	print('Loading 20newsgroup dataset for all categories')

	############################# Load train data
	train = fetch_20newsgroups(subset='train')
	train_data = [preprocessor(doc) for doc in train.data]
	save_pickle(train_data, 'dataset/train-data.pkl')
	train_data = load_pickle('dataset/train-data.pkl')[:]
	train_target = train.target[:]

	print('Train data:\n')
	print('%d documents' % len(train.filenames))
	print('%d categories' % len(train.target_names))

	############################# Preprocess 
	preprocess = Pipeline([
		('count', CountVectorizer(max_df=.8, min_df=3, ngram_range=(1, 3), max_features=10000)),
		('tfidf', TfidfTransformer())
	])

	############################# Cross validation
	C = np.linspace(1, 3, 10)

	# C = np.logspace(-5, 2, 10)

	val_dir = 'C = np.linspace(1, 3, 10)'
	make_dir('result/svm/%s' % val_dir)

	clf = LinearSVC(max_iter=500)
	estimator = Pipeline([
		('pre', preprocess),
		('clf', clf) 
	])
	parameters = {
	    'clf__C': C
	}

	grid_search = GridSearchCV(estimator, parameters, n_jobs=3, verbose=1)
	grid_search.fit(train_data, train_target)
	print(grid_search.cv_results_)
	mean_train_score = grid_search.cv_results_['mean_train_score']
	mean_val_score = grid_search.cv_results_['mean_test_score']
	# Plot
	plt.xlabel('C')
	plt.ylabel('Score')
	plt.plot(C, mean_train_score, c='r', label='Training score')
	plt.plot(C, mean_val_score, c='b', label='Validation score')
	plt.legend()
	plt.savefig('result/svm/%s/val_curve.png' % val_dir)
	plt.show()

	best_estimator = grid_search.best_estimator_ 
	save_pickle(best_estimator, 'result/svm/estimator.pkl')

	############################# Test
	best_estimator = load_pickle('result/svm/estimator.pkl')

	# Load test data
	test = fetch_20newsgroups(subset='test')
	test_data = [preprocessor(doc) for doc in test.data]
	save_pickle(test_data, 'dataset/test-data.pkl')
	test_data = load_pickle('dataset/test-data.pkl')[:]
	test_target = test.target[:]

	t0 = time()
	test_pred = best_estimator.predict(test_data)
	predict_time = time() - t0
	with open('result/svm/report', 'w') as f:
		f.write('Best estimator:\n')
		f.write(str(best_estimator.get_params()))
		f.write('\n\n\n')
		f.write(classification_report(test_target, test_pred))
		f.write('\n\n\n')
		f.write('Predict time: %f' % predict_time)
	############################# Learning curve
	# print(best_estimator.get_params()['pre'].get_params()['count'].vocabulary_)
	n_train = len(train_target)
	f1 = []
	percent = [.2, .4, .6, .8, 1.]
	for r in percent:
		n = int(r * n_train)
		best_estimator.fit(train_data[:n], train_target[:n])

		test_pred = best_estimator.predict(test_data)
		f1.append(f1_score(test_target, test_pred, average='macro'))
	save_pickle((percent, f1), 'result/svm/learning')

	# Plot
	plt.xlabel('Part of train data')
	plt.ylabel('F1 score')
	plt.plot(percent, f1, c='r', label='Test score')
	plt.legend()
	plt.savefig('result/svm/learning_curve.png')
	plt.show()
