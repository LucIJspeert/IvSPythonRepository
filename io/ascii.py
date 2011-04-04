# -*- coding: utf-8 -*-
"""
Read and write ASCII files.
"""
import gzip
import logging

import numpy as np

logger = logging.getLogger("IO.ASCII")

#{ Input
def read2list(filename,**kwargs):
    """
    Load an ASCII file to list of lists.
    
    The comments and data go to two different lists.
    
    Also opens gzipped files.
    
    @param filename: name of file with the data
    @type filename: string
    @keyword commentchar: character(s) denoting comment rules
    @type commentchar: list of str
    @keyword splitchar: character seperating entries in a row (default: whitespace)
    @type splitchar: str or None
    @return: list of lists (data rows)
             list of lists (comments lines without commentchar),
    @rtype: (list,list)
    """
    commentchar = kwargs.get('commentchar',['#'])
    splitchar = kwargs.get('splitchar',None)
    
    if os.path.splitext(filename)[1] == '.gz':
        ff = gzip.open(filename)
    else:
        ff = open(filename)
        
    data = []  # data
    comm = []  # comments
    
    while 1:  # might call read several times for a file
        line = ff.readline()
        if not line: break  # end of file
        
        #-- when reading a comment line
        if line[0] in commentchar:
            comm.append(line[1:].strip())
            continue # treat next line
        
        #-- when reading data, split the line
        data.append(line.split(splitchar))
    ff.close()
    
    #-- report that the file has been read
    logger.debug('Data file %s read'%(filename))
    
    #-- and return the contents
    return data,comm

def read2array(filename,**kwargs):
    """
    Load ASCII file to a numpy array.
    
    For a list of extra keyword arguments, see C{<read2list>}.
    
    @param filename: name of file with the data
    @type filename: string
    @keyword dtype: type of numpy array (default: float)
    @type dtype: numpy dtype
    @keyword return_comments: flag to return comments (default: False)
    @type return_comments: bool
    @return: data array (, list of comments)
    @rtype: ndarray (, list)
    """
    dtype = kwargs.get('dtype',np.float)
    return_comments = kwargs.get('return_comments',False)
    data,comm = read2list(filename,**kwargs)
    return np.array(data,dtype=dtype)
    return return_comments and (data,comments) or data



#}

#{ Output

def write_array(data, filename, **kwargs):
    """
    Save a numpy array to an ASCII file.
    """
    header = kwargs.get('header',[])
    comments = kwargs.get('comments',None)
    sep = kwargs.get('sep',' ')
    
    

#}