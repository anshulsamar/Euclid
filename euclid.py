from lxml import html
import requests
from bs4 import BeautifulSoup  
import pdb
import concept
import link
import numpy as np
import scipy.cluster.vq as vq
import sys
import pickle
import os
import string
import operator

def justificationToLink(just):

    linkList = []
    just = just.replace('(','').replace(')','').replace('\r','')
    justList = just.split('\n')
    justListTemp = []
    justListTemp2 = []
    for j in justList:
        justListTemp.extend(j.split(','))
    for j in justListTemp:
        if 'Post. ' in j:
            continue
        else:
            justListTemp2.extend(j.split(' '))
    justList = justListTemp2
    print justList
    for j in justList:

        comp = j.replace(',','').replace(' ','').split('.')
        print comp
        if comp[0] in ['','\r','Above','Cor','.','As','in','as','or','converse','and','to']:
            continue
        elif (comp[0] == '13'): #one edge case in book 7
            print "Book 7 edge"
            l = link.Link('Def',7,13)
            linkList.append(l)
        elif comp[0] == 'C':
            if len(comp) == 3 and len(comp[2]) > 0:
                l = link.Link('Com',1,int(comp[2]))
                linkList.append(l)
            else:
                for i in range(1,6):
                    l = link.Link('Com',1,i)
                    linkList.append(l)
        elif comp[0] == 'Post' or comp[1] == 'Post':    
            l = link.Link('Pos',1,int(comp[-1]))
            linkList.append(l)
        elif comp[0] == 'Def':
            book = romanToBook(comp[1])
            l = link.Link('Def',book,int(comp[2]))
            linkList.append(l)
        elif comp[1] == 'Def':
            book = romanToBook(comp[0])
            l = link.Link('Def',book,int(comp[2]))
            linkList.append(l)
        else:
            book = romanToBook(comp[0])
            l = link.Link('Pro',book,int(comp[1]))
            linkList.append(l)

    return linkList

def romanToBook(book):

    suf = 0

    if book == "I":
        suf = 1
    if book == "II":
        suf = 2
    if book == "III":
        suf = 3
    if book == "IV":
        suf = 4
    if book == "V":
        suf = 5
    if book == "VI":
        suf = 6
    if book == "VII":
        suf = 7
    if book == "VIII":
        suf = 8
    if book == "IX":
        suf = 9
    if book == "X":
        suf = 10
    if book == "XI":
        suf = 11
    if book == "XII":
        suf = 12
    if book == "XIII":
        suf = 13

    return suf

def bookToRoman(book):

    suf = ""

    if book == 1:
        suf = "I"
    if book == 2:
        suf = "II"
    if book == 3:
        suf = "III"
    if book == 4:
        suf = "IV"
    if book == 5:
        suf = "V"
    if book == 6:
        suf = "VI"
    if book == 7:
        suf = "VII"
    if book == 8:
        suf = "VIII"
    if book == 9:
        suf = "IX"
    if book == 10:
        suf = "X"
    if book == 11:
        suf = "XI"
    if book == 12:
        suf = "XII"
    if book == 13:
        suf = "XIII"

    return suf

def load(book):

    Definitions = []
    Propositions = []
    suf = bookToRoman(book)
    base_url = "http://aleph0.clarku.edu/~djoyce/java/elements/"
    url = base_url+"book"+suf+"/"+"book"+suf+".html"
    page = requests.get(url)
    soup = BeautifulSoup(page.text)

    for conceptType in soup.find_all('dl'): #[0].find_all('dd'):
        prev = conceptType.previous_element.previous_element
        if prev == 'Definitions' or prev == "Common Notions" or prev == "Postulates":
            i = 1
            for dd in conceptType.find_all('dd'):
                Definitions.append(concept.Concept(prev[0:3],book,i,dd.get_text().replace('\r','').replace('\n',""),"",[],[]))
                i += 1
        if prev == 'Propositions':
            count = 0
            for a in conceptType.find_all('b'):
                if "Proposition" in str(a):
                    count += 1
            for i in range(1,count+1):
                url = base_url + "book" + suf + "/prop" + suf + str(i) + ".html"
                page = requests.get(url)
                soup = BeautifulSoup(page.text)
                print url
                statement = soup.find_all('div',class_='statement')[0].get_text()
                text = ""
                fromLink = []
                for p in soup.find('div',class_='theorem').find_all('p'):
                    text += p.get_text()
                for j in soup.find('div',class_='theorem').find_all('div',class_='just'):
                    for l in justificationToLink(j.get_text()):
                        fromLink.append(l)
                Propositions.append(concept.Concept("Pro",book,i,statement.replace('\r','').replace('\n',''),text.replace('\r','').replace('\n',''),[],fromLink))
                
    return [Definitions,Propositions]

def createMatrix(collection):

    rowDimension = 0
    colDimension = 0
    for book in collection:
        rowDimension += len(book[0]) + len(book[1])
        colDimension += len(book[1])

    M = np.zeros((rowDimension,colDimension))

    for book in collection:
        a = []
        a.extend(book[0])
        a.extend(book[1])
        for concept in a:
            if (concept.category == "Pro"):
                index = collectionToMatrixCol(concept.book,concept.number,collection)
                for link in concept.fromLink:
                    linkIndex = collectionToMatrixRow(link.book,link.category,link.number,collection)              
                    M[linkIndex,index] = 1

    return M

def collectionToMatrixRow(book, category, number,collection):
    if category == 'Pos':
        number = number + 23
    if category == 'Com':
        number = number  + 5 + 23
    a = 0
    for i in range(0,book-1):
        a += len(collection[i][0]) + len(collection[i][1])
    if category == 'Pro':
        a += len(collection[book-1][0])
    return a + number -1    

def collectionToMatrixCol(book, number,collection):
    a = 0
    for i in range(0,book-1):
        a += len(collection[i][1])
    return a + number -1    

def matrixColToCollection(index,collection):

    a = 0
    for i in range(0,len(collection)):
        total = len(collection[i][1])
        if ((index - a) < total):
            return [i+1,'Pro',index-a+1]
        else:
            a += total

def matrixRowToCollection(index,collection):
    a = 0
    for i in range(0,len(collection)):
        total = len(collection[i][0]) + len(collection[i][1])
        if ((index - a) < total):
            if ((index -a) < len(collection[i][0])):
                if (i == 0):
                    category = ""
                    if (index-a +1 <= 23):
                        category = "Def"
                    elif (index-a+1 <= 23 + 5):
                        category = "Pos"
                    else:
                        category = "Com"
                    return [i+1,category,index-a+1]
                else:    
                    return [i+1,'Def',index-a+1]
            else:
                a += len(collection[i][0])
                return [i+1,'Pro',index-a+1]
        else:
            a += total

    #0 1 2 3 | 4 5 6 | 7 8 | 9 10 11 12 (matrix indexing)
    #1 2 3 4 | 1 2 3 | 1 2 | 1 2  3  4 (collection indexing)

def simpleStatistics(matrix,collection,start,end):

    print "General Statistics"
    print "------------------"
    columnSum = np.sum(matrix[:,start:end],0)
    maxLinks = np.argmax(columnSum)
    print matrixColToCollection(maxLinks+start,collection)
    print "Max number of links: " + str(np.max(columnSum))
    averageLinks = np.sum(columnSum)/np.size(columnSum)
    print "Average links: " + str(averageLinks)
    rowSum = np.sum(np.transpose(matrix[:,start:end]),0)
    maxLinked = np.argmax(rowSum)
    print matrixRowToCollection(maxLinked,collection)
    print "Max linked number: " + str(np.max(rowSum))
    averageLinked = np.sum(rowSum)/np.size(rowSum)
    print "Average linked: " + str(averageLinked)

def topWords(matrix, collection,start,end,books,cluster):

    maxLength = 0
    maxLengthProp = None
    totalLength = 0
    statementLexicon = dict()
    textLexicon = dict()

    for b in books:
        for prop in collection[b-1][1]:
            statement = prop.statement
            text = prop.text
            length = len(text)
            totalLength += length
            if length > maxLength:
                maxLengthProp = prop
                maxLength = length
            #statement = "".join(ch for ch in statement if ch not in exclude)
            statement = statement.lower()
            for p in ['.',',','!',':']:
                statement = statement.replace(p,' ')
            words = statement.split(' ')
            for w in words:
                if w != "" and w != " ":
                    if w not in statementLexicon:
                        statementLexicon[w] = 1
                    else:
                        statementLexicon[w] = statementLexicon[w] + 1
            #text = "".join(ch for ch in text if ch not in exclude)
            text = text.lower()
            for p in ['.',',','!',':']:
                text = text.replace(p,' ')
            words = text.split(' ')
            for w in words:
                if w != "" and w != " ":
                    if w not in textLexicon:
                        textLexicon[w] = 1
                    else:
                        textLexicon[w] = textLexicon[w] + 1
    
    sortedStatementLexicon = sorted(statementLexicon.items(), key=operator.itemgetter(1),reverse=True)
    sortedTextLexicon = sorted(textLexicon.items(), key=operator.itemgetter(1),reverse=True)

    print [maxLengthProp.book, "Pro", maxLengthProp.number]
    print "Maximum length text: " + str(maxLength)

    exclude = ["of","and","the","on","to","is",'in','a','f','b','d','e','if','as','that','c','are','also','g','h','k','bye','by','it','which','then']

    numTop = 10
    i = 0
    j = 0
    print "Top " + str(numTop) + " Words in Statement"
    print "------------------"
    while i < numTop:
        item = sortedStatementLexicon[j]
        if (item[0] not in exclude):
            print item[0] + " " + str(item[1])
            i += 1
        j += 1

    numTop = 10
    i = 0
    j = 0
    print "Top " + str(numTop) + " Words in Text"
    print "------------------"
    while i < numTop:
        item = sortedTextLexicon[j]
        if (item[0] not in exclude):
            print item[0] + " " + str(item[1])
            i += 1
        j += 1    

    if cluster == 0:
        return

    print "Text based K Means Cluster"
    print "-----------------------------"

    features = [item[0] for item in sortedTextLexicon]
    lexMat = np.zeros((len(features),matrix[:,start:end].shape[1]))
    i = 0

    for b in books:
        for prop in collection[b-1][1]:
            index = collectionToMatrixCol(prop.book,prop.number,collection)
            if (index-start != i):
                print "Error"
            i += 1            
            text = prop.text.lower()
            for p in ['.',',','!',':']:
                text = text.replace(p,' ')
            words = text.split(' ')
            for w in words:
                if w != "" and w != " ":
                    lexMat[features.index(w), index-start] += 1

    clusterNum = 5
    [codebook, distortion] = vq.kmeans(vq.whiten(lexMat.T),clusterNum)
    clusterAssignments = vq.vq(lexMat.T, codebook)  
    indexes = np.argsort(clusterAssignments[0])
    startIndex = 0

    for i in range(0, clusterNum):
        print "Category " + str(i)
        count = clusterAssignments[0].tolist().count(i)
        print sorted(indexes.tolist()[startIndex:startIndex+count])
        startIndex = startIndex+count

    print "Links based K Means Cluster"
    print "-----------------------------"

    clusterNum2 = 5
    #nan if I whiten? Therefore, not whitening even though it is recommended
    [codebook2, distortion2] = vq.kmeans(matrix[start:end].T,clusterNum2)
    clusterAssignments2 = vq.vq(matrix[start:end].T, codebook2)

    startIndex = 0
    indexes2 = np.argsort(clusterAssignments2[0])

    for i in range(0, clusterNum2):
        print "Category " + str(i)
        count = clusterAssignments2[0].tolist().count(i)
        print sorted(indexes2.tolist()[startIndex:startIndex+count])
        startIndex = startIndex+count



def oldCode():
    
    for i in range(0,lexMat.shape[1]):
        minDistance =  np.linalg.norm(lexMat[:,1] - codebook[0,:])
        minCluster = 0
        for k in range(0,codebook.shape[0]):
            distance = np.linalg.norm(lexMat[:,1] - codebook[k,:].T) 
            print distance
            if distance < minDistance:
                minCluster = k
                minDistance = distance
        clusterAssignments.append(minCluster)

def svd(matrix,collection,start,end):
    
    print "Singular Value Decomposition"
    print "----------------------------"
    U, s, V = np.linalg.svd(matrix[:,start:end],full_matrices=False)
    if (np.allclose(matrix[:,start:end],np.dot(U,np.dot(np.diag(s),V))) == False):
        print "Error"
    print s

    #Rank 1 approximation
    matrix1 = np.outer(U[:,0],np.dot(s[0],V[0,:]))

    #Spanning vectors in rank 1, 2, 3 approximations
    firstVector = np.dot(U[:,0],s[0])
    secondVector = np.dot(U[:,1],s[1])
    thirdVector = np.dot(U[:,2],s[2])
    print firstVector
    print secondVector
    print thirdVector

def main():

    np.set_printoptions(precision=4,suppress=True)
    collection = []
    maxBook = 9

    if (os.path.isfile('collection.p')):
        collection = pickle.load(open('collection.p','rb'))
    else:
        for book in range(1,maxBook+1):
            collection.append(load(book))
        pickle.dump(collection,open('collection.p','wb'))

    matrix = []

    if (os.path.isfile('matrix.p')):
        matrix = pickle.load(open('matrix.p','rb'))
    else:
        matrix = createMatrix(collection)
        pickle.dump(matrix,open('matrix.p','wb'))

    for i in range(0,maxBook):
        print "Book " + str(i+1)
        start = 0
        for j in range(0,i):
            start += len(collection[j][1])
        #simpleStatistics(matrix,collection,start,start+len(collection[i][1]))
        topWords(matrix,collection,start,start+len(collection[i][1]),[i+1],0)
        #svd(matrix,collection,start,start+len(collection[i][1]))

if __name__ == '__main__':

    main()
