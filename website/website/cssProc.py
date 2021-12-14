from .db import engine_nl

def getStandardRunList():
    conn = engine_nl.connect()
    result = conn.execute("SELECT run_number FROM cssproc WHERE standard_run = %s ORDER BY run_number DESC",('t'))
    info = result.fetchall()
    return [i[0] for i in info]

def pull_down_test_scores(run_number):
    conn = engine_nl.connect()
    result = conn.execute("SELECT kstest_highocc,kstest_lowocc,chisqtest_highocc,chisqtest_lowocc FROM cssproc WHERE run_number = %s",(run_number))
    info = result.fetchall()
    return info[0]
    
class Info:
    '''Class to hold run info
    '''
    def __init__(self,run):
        self.standRunList = getStandardRunList()
        self.currentRun = run
        if run ==-1:
            self.highOccKStest, self.lowOccKStest, self.highOccChisq, self.lowOccChisq = 0,0,0,0
        else:
            self.highOccKStest, self.lowOccKStest, self.highOccChisq, self.lowOccChisq = pull_down_test_scores(run)

        self.highOccTests ={"ChiSq test":self.highOccChisq,"KS test":self.highOccKStest}
        self.lowOccTests ={"ChiSq test":self.lowOccChisq,"KS test":self.lowOccKStest}

    def getLastStandRun(self):
        """Gets the standard run before the current run.
        """
        if self.standRunList.index(self.currentRun)==0:
            return self.currentRun
        else:
            return self.standRunList[self.standRunList.index(self.currentRun)-1]

    def getNextStandRun(self):
        """Gets the standard run after the current run.
        """
        if self.standRunList.index(self.currentRun)==len(self.standRunList)-1:
            return self.currentRun
        else:
            return self.standRunList[self.standRunList.index(self.currentRun)+1]
