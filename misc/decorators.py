# -*- coding: utf-8 -*-
"""
Various decorator functions
    - Memoization with args and kwargs (@memoized)
    - Make a parallel version of a function (@make_parallel)
    - Retry with exponential backoff (@retry(3,2))
    - Retry accessing website with exponential backoff (@retry(3,2))
    - Counting function calls (@countcalls)
    - Timing function calls
    - Redirecting print statements to logger
    - Disable-decorator decorator
"""
import functools
import cPickle
import time
import logging
import sys
import math
import socket

memory = {}

#{ Common tools
def memoized(fctn):
    """
    Cache a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    @functools.wraps(fctn)
    def memo(*args,**kwargs):
        haxh = cPickle.dumps((fctn.__name__, args, sorted(kwargs.iteritems())))
        modname = fctn.__module__
        if not (modname in memory):
            memory[modname] = {}
        if not (haxh in memory[modname]):
            memory[modname][haxh] = fctn(*args,**kwargs)
        return memory[modname][haxh]
    if memo.__doc__:
        memo.__doc__ = "\n".join([memo.__doc__,"This function is memoized."])
    return memo

def clear_memoization():
    """
    Clear contents of memory
    """
    for key in memory.keys():
        del memory[key]
    print("Memoization cleared")

def make_parallel(fctn):
    """
    Make a parallel version of a function.
    
    This extends the function's arguments with one extra argument, which is
    a parallel array that collects the output of the function.
    
    You have to decorate this function in turn with a function that calls the
    basic function, but with different arguments so to effectively make it
    parallel (e.g. in the frequency analysis case, this would be a function
    that calls the periodogram calculation with different f0 and fn.
    """
    @functools.wraps(fctn)
    def extra(*args,**kwargs):
        arr = args[-1] # this is the parallel array
        out = fctn(*args[:-1],**kwargs)
        arr.append(out) # collect the output
    return extra

def timeit(fctn):
    """
    Time a function.
    
    @return: output from func, duration of function
    @rtype: 2-tuple
    """
    @functools.wraps(fctn)
    def time_this(*args,**kwargs):
        start_time = time.time()
        output = fctn(*args,**kwargs)
        duration = time.time()-start_time
        print "FUNC: %s MOD: %s: EXEC TIME: %.3fs"%(fctn.__module__,fctn.__name__,duration)    
        return output
    return time_this

def retry(tries, delay=3, backoff=2):
  """
  Retry a function or method until it returns True.
  
  Delay sets the initial delay, and backoff sets how much the delay should
  lengthen after each failure. backoff must be greater than 1, or else it
  isn't really a backoff. tries must be at least 0, and delay greater than 0.
  """

  if backoff <= 1:
    raise ValueError("backoff must be greater than 1")

  tries = math.floor(tries)
  if tries < 0:
    raise ValueError("tries must be 0 or greater")

  if delay <= 0:
    raise ValueError("delay must be greater than 0")

  def deco_retry(f):
    def f_retry(*args, **kwargs):
      mtries, mdelay = tries, delay # make mutable

      rv = f(*args, **kwargs) # first attempt
      while mtries > 0:
        if rv == True: # Done on success
          return True

        mtries -= 1      # consume an attempt
        time.sleep(mdelay) # wait...
        mdelay *= backoff  # make future wait longer

        rv = f(*args, **kwargs) # Try again

      return False # Ran out of tries :-(

    return f_retry # true decorator -> decorated function
  return deco_retry  # @retry(arg[, ...]) -> true decorator

def retry_http(tries, backoff=2, on_failure='error'):
    """
    Retry a function or method reading from the internet until no socket or IOError
    is raised
    
    delay sets the initial delay, and backoff sets how much the delay should
    lengthen after each failure. backoff must be greater than 1, or else it
    isn't really a backoff. tries must be at least 0, and delay greater than 0.
    """
    delay = socket.getdefaulttimeout()
    o_delay = socket.getdefaulttimeout()
    if backoff <= 1:
      raise ValueError("backoff must be greater than 1")

    tries = math.floor(tries)
    if tries < 0:
      raise ValueError("tries must be 0 or greater")

    if delay <= 0:
      raise ValueError("delay must be greater than 0")

    def deco_retry(f):
      def f_retry(*args, **kwargs):
        mtries, mdelay = tries, delay # make mutable
        
        while mtries > 0:
          try:
              rv = f(*args, **kwargs) # Try again
          except IOError,msg:
              rv = False
          except socket.error:
              rv = False
              
          if rv != False: # Done on success
            return rv
          mtries -= 1      # consume an attempt
          socket.setdefaulttimeout(mdelay) # wait...
          mdelay *= backoff  # make future wait longer
          print "URL timeout: %d attempts remaining (delay=%.1fs)"%(mtries,mdelay)
        print "URL timeout: number of trials exceeded"
        if on_failure=='error':
          raise IOError,msg # Ran out of tries :-(
        else:
          print "Failed, but continuing..."
          return None

      return f_retry # true decorator -> decorated function
    socket.setdefaulttimeout(o_delay)
    return deco_retry  # @retry(arg[, ...]) -> true decorator

class countcalls(object):
   """
   Keeps track of the number of times a function is called.
   """
   __instances = {}

   def __init__(self, f):
      self.__f = f
      self.__numcalls = 0
      countcalls.__instances[f] = self

   def __call__(self, *args, **kwargs):
      self.__numcalls += 1
      return self.__f(*args, **kwargs)

   @staticmethod
   def count(f):
      """Return the number of times the function f was called."""
      return countcalls.__instances[f].__numcalls

   @staticmethod
   def counts():
      """Return a dict of {function: # of calls} for all registered functions."""
      return dict([(f, countcalls.count(f)) for f in countcalls.__instances])

class LogPrinter:
    """
    LogPrinter class which serves to emulates a file object and logs
    whatever it gets sent to a Logger object at the INFO level.
    """
    def __init__(self):
        """Grabs the specific logger to use for logprinting."""
        self.ilogger = logging.getLogger('logprinter')
        il = self.ilogger
        logging.basicConfig()
        il.setLevel(logging.INFO)
    
    def write(self, text):
        """Logs written output to a specific logger"""
        text = text.strip()
        if text: self.ilogger.info(text)

def logprintinfo(func):
    """
    Wraps a method so that any calls made to print get logged instead
    """
    def pwrapper(*arg,**kwargs):
        stdobak = sys.stdout
        lpinstance = LogPrinter()
        sys.stdout = lpinstance
        try:
            return func(*arg,**kwargs)
        finally:
            sys.stdout = stdobak
    return pwrapper
#}

#{ Disable decorator
def disabled(func):
    """
    Disables the provided function
    
    use as follows:
        1. set a global enable flag for a decorator:
        >>> global_mydecorator_enable_flag = True
    
        2. toggle decorator right before the definition
        >>> state = mydecorator if global_mydecorator_enable_flag else disabled
        >>> @state
    """
    return func
#}

#{ Module specific
def parallel_periodogram(fctn):
    """
    Run periodogram calculations in parallel.
    
    This splits up the frequency range between f0 and fn in 'threads' parts.
    
    This must decorate a 'make_parallel' decorator.
    """
    @functools.wraps(fctn)
    def globpar(*args,**kwargs):
        #-- construct a manager to collect all calculations 
        manager = Manager() 
        arr = manager.list([]) 
        all_processes = [] 
        f0 = kwargs['f0']
        fn = kwargs['fn']
        threads = float(kwargs.get('threads',1))
        
        #-- extend the arguments to include the parallel array
        myargs = tuple(list(args) + [arr] )
        
        #-- distribute the periodogram calcs over different threads, and wait
        for i in range(int(threads)):
            #-- define new start and end frequencies
            kwargs['f0'] = f0 + i*(fn-f0) / threads
            kwargs['fn'] = f0 +(i+1)*(fn-f0) / threads
            logger.debug("parallel: starting process %s: f=%.4f-%.4f"%(i,kwargs['f0'],kwargs['fn']))
            p = Process(target=fctn, args=myargs, kwargs=kwargs) 
            p.start()
            all_processes.append(p) 
        
        for p in all_processes: p.join() 
        
        logger.debug("parallel: all processes ended") 
        
        #-- join all periodogram pieces 
        freq = np.hstack([output[0][0] for output in arr])
        ampl = np.hstack([output[0][1] for output in arr]) 
        sort_arr = np.argsort(freq)
        ampl = ampl[sort_arr] 
        freq = freq[sort_arr]
        ampl[np.isnan(ampl)] = 0.
        
        if len(output)>1:
            ret_value = tuple([(freq,ampl)] + list(output[1:]))
        else:
            ret_value = (freq,ampl)
        
        return ret_value
        
    return globpar

#}