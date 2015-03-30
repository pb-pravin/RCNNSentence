import sys
import numpy as np

from model import *
from loadWordVec import *

def parseSentence(text,wordIndex,maxLen):
	'''
	>>>convert sentence to a matrix

	>>>type text:string
	>>>para text:raw text
	>>>type wordIndex:dict
	>>>para wordIndex:map word to its entry
	>>>type maxLen:int
	>>>para maxLen:maximum length of sentences in the whole set
	'''
	length=len(text)
	padLeft=(maxLen-length+1)/2
	padRight=(maxLen-length)/2
	vec=[]

	for i in xrange(padLeft):
		vec.append(0)
	for word in text:
		vec.append(wordIndex[word])
	for i in xrange(padRight):
		vec.append(0)

	assert len(vec)==maxLen
	return vec

def loadDatas(dataFile,wordVecFile='',dimension=300,rand=False):
	'''
	>>>load training/validate/test data and wordVec info

	>>>type dataFile/wordVecFile: string
	>>>para dataFile/wordVecFile: data and wordVec file
	>>>type dimension: int
	>>>para dimension: the dimension of word embeddings
	>>>type static: bool
	>>>para static: static wordVec or not
	'''
	fopen=open(dataFile,'rb')
	data=cPickle.load(fopen)
	fopen.close()
	sentences,vocab,config=data
		
	wordVec=[]
	if rand==False:
		vectors,wordIndex=getWordVec(dataFile,wordVecFile)
	else:
		vectors,wordIndex=getRandWordVec(dataFile,dimension)

	return sentences,vocab,config,vectors,wordIndex

def parseConfig(sentences,vocab,config,vectors,wordIndex,static):
	'''
	>>>load configs to generate model and train/validate/test batches

	>>>sentences/vocab/config/vectors/wordIndex is the same in README.md file of each dataset
	>>>type static:bool
	>>>para static:whether or not to use static wordVec
	'''
	categories=config['classes']
	sets=config['all']
	train=config['train']
	test=config['test']
	cross=config['cross']
	dimension=len(vectors[0])
	batchSize=25

	maxLen=0
	for sentence in sentences:
		length=len(sentence['text'])
		if length>maxLen:
			maxLen=length

	setMatrix={}
	setLabel={}
	for subset in sets:
		setMatrix[subset]=[]
		setLabel[subset]=[]

	for sentence in sentences:
		vec=parseSentence(sentence['text'],wordIndex,maxLen)
		setLabel=sentence['setLabel']
		category=sentence['label']
		setMatrix[setLabel].append(vec)
		setLabel[setLabel].append(category)

	if cross==False:
		print 'final minimum precision %f%%'%((1.0-minError)*100)
		network=model(
			wordMatrix=vectors,
			shape=(batchSize,1,maxLen,dimension),
			filters=(3,4,5),
			rfilter=(5,1),
			features=(100),
			time=4,categories=categories,
			static=static,
			dropoutRate=(0.5),
			learningRate=0.01
		)

		trainSet={},trainSetX=[],trainSetY=[]
		validateSet={},validateSetX=[],validateSetY=[]
		testSet={},testSetX=[],testSetY=[]
		for subset in train:
			trainSetX+=setMatrix[subset]
			trainSetY+=setLabel[subset]
		for subset in test:
			testSetX+=setMatrix[subset]
			testSetY+=setLabel[subset]


		if len(trainSetX)%batchSize>0:
			extraNum=batchSize-len(trainSetX)%batchSize
			extraIndex=np.random.permutation(range(len(trainSetX)))
			for i in xrange(extraNum):
				trainSetX.append(trainSetX[extraIndex[i]])
				trainSetY.append(trainSetY[extraIndex[i]])

		trainSize=len(trainSetX)
		validateSize=trainSize/5-(trainSize/5)%batchSize
		validateIndex=np.random.permutation(range(trainSize))
		for i in xrange(validateSize):
			validateSetX.append(trainSetX[validateIndex[i]])
			validateSetY.append(trainSetY[validateIndex[i]])

		trainSet['x']=np.array(trainSetX,dtype='int')
		trainSet['y']=np.array(trainSetY,dtype='int')
		validateSet['x']=np.array(validateSetX,dtype='int')
		validateSet['y']=np.array(validateSetY,dtype='int')
		testSet['x']=np.array(testSetX,dtype='int')
		testSet['y']=np.array(testSetY,dtype='int')

		minError=model.train_validate_test(trainSet,validateSet,testSet)
	else:
		minErrors=[]
		for item in sets:
			network=model(
				wordMatrix=vectors,
				shape=(batchSize,1,maxLen,dimension),
				filters=(3,4,5),
				rfilter=(5,1),
				features=(100),
				time=4,categories=categories,
				static=static,
				dropoutRate=(0.5),
				learningRate=0.01
			)

			trainSet={},trainSetX=[],trainSetY=[]
			validateSet={},validateSetX=[],validateSetY=[]
			testSet={},testSetX=[],testSetY=[]
			for subset in sets:
				if item!=subset:
					trainSetX+=setMatrix[subset]
					trainSetY+=setLabel[subset]
				else:
					testSetX+=setMatrix[subset]
					testSetY+=setLabel[subset]

			if len(trainSetX)%batchSize>0:
				extraNum=batchSize-len(trainSetX)%batchSize
				extraIndex=np.random.permutation(range(len(trainSetX)))
				for i in xrange(extraNum):
					trainSetX.append(trainSetX[extraIndex[i]])
					trainSetY.append(trainSetY[extraIndex[i]])

			trainSize=len(trainSetX)
			validateSize=trainSize/5-(trainSize/5)%batchSize
			validateIndex=np.random.permutation(range(trainSize))
			for i in xrange(validateSize):
				validateSetX.append(trainSetX[validateIndex[i]])
				validateSetY.append(trainSetY[validateIndex[i]])

			trainSet['x']=np.array(trainSetX,dtype='int')
			trainSet['y']=np.array(trainSetY,dtype='int')
			validateSet['x']=np.array(validateSetX,dtype='int')
			validateSet['y']=np.array(validateSetY,dtype='int')
			testSet['x']=np.array(testSetX,dtype='int')
			testSet['y']=np.array(testSetY,dtype='int')

			minError=model.train_validate_test(trainSet,validateSet,testSet)
			minErrors.append(minError)
		print 'Final Precision Rate %f%%'%((1.-np.mean(minErrors))*100)

if __name__=='__main__':
	static=False
	rand=False
	mode=0
	dataFile=''
	vecFile=''

	for i in xrange(len(sys.argv)):
		if sys.argv[i]=='-d':
			mode=1
		elif sys.argv[i]=='-v':
			mode=2
		else:
			if mode==1:
				dataFile=sys.argv[i]
				mode=0
			elif mode==2:
				vecFile=sys.argv[i]
				mode=0
			else:
				if sys.argv[i]=='-nonstatic':
					static=False
				elif sys.argv[i]=='-static':
					static=True
				elif sys.argv[i]=='-rand':
					rand=True
				elif sys.argv[i]=='-word2vec':
					rand=False
				else:
					raise Error('command line error')
	print 'config: dataFile:%s, vecFile:%s, static:%r, rand:%r'%(dataFile,vecFile,static,rand)

	sentences,vocab,config,vectors,wordIndex=loadDatas(dataFile=dataFile,wordVecFile=vecFile,dimension=300,rand=rand)
	parseConfig(sentences,vocab,config,vectors,wordIndex,static)