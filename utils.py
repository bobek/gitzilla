
"""
utils module for gitzilla

"""

import os
import sys
import subprocess
import bugz.bugzilla


sNoCommitRev = "0000000000000000000000000000000000000000"

def execute(asCommand, bSplitLines=False, bIgnoreErrors=False):
  """
  Utility function to execute a command and return the output.
  """
  p = subprocess.Popen(asCommand,
                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       shell=False,
                       close_fds=True,
                       universal_newlines=True,
                       env=None)
  if bSplitLines:
    data = p.stdout.readlines()
  else:
    data = p.stdout.read()
  iRetCode = p.wait()
  if iRetCode and not bIgnoreErrors:
    print >>sys.stderr, 'Failed to execute command: %s\n%s' % (asCommand, data)
    sys.exit(-1)

  return data


def init_bugzilla(sBZUrl, sBZUser, sBZPasswd):
  """
  initializes and returns a bugz.bugzilla.Bugz instance.

  This may be overridden in custom hook scripts in order to expand auth
  support.
  """
  if sBZUrl is None:
    raise ValueError("No Bugzilla URL specified")

  oBZ = bugz.bugzilla.Bugz(sBZUrl, user=sBZUser, password=sBZPasswd)
  return oBZ



def get_changes(sOldRev, sNewRev, sFormatSpec, sSeparator, bIncludeDiffStat, sRefName):
  """
  returns an array of chronological changes, between sOldRev and sNewRev,
  according to the format spec sFormatSpec.
  """
  if sOldRev == sNoCommitRev:
    sCommitRange = sNewRev
  elif sNewRev == sNoCommitRev:
    sCommitRange = sOldRev
  else:
    sCommitRange = "%s..%s" % (sOldRev, sNewRev)

  sFormatSpec = sFormatSpec.strip("\n").replace("\n", "%n")

  if bIncludeDiffStat:
    sCommand = "whatchanged"
  else:
    sCommand = "log"

  asCommand = ['git', sCommand,
               "--format=format:%s%s" % (sSeparator, sFormatSpec)]

  if sRefName != None and sRefName.startswith('refs/heads/'):
    asAllBranches = execute(['git', 'for-each-ref', '--format=%(refname)',
                             'refs/heads/'], bSplitLines=True             )
    asAllBranches = map(lambda x: x.strip(), asAllBranches)
    asOtherBranches = filter(lambda x: x != sRefName, asAllBranches)
    asNotOtherBranches = execute(['git', 'rev-parse', '--not']
                                 + asOtherBranches, bSplitLines=True)
    asNotOtherBranches = map(lambda x: x.strip(), asNotOtherBranches)
    asCommand += asNotOtherBranches

  asCommand.append(sCommitRange)
  sChangeLog = execute(asCommand)
  asChangeLogs = sChangeLog.split(sSeparator)
  asChangeLogs.reverse()

  return asChangeLogs[:-1]



def post_to_bugzilla(iBugId, sComment, sBZUrl, sBZUser, sBZPasswd):
  """
  posts the comment to the given bug id.
  """
  if sBZUrl is None:
    raise ValueError("No Bugzilla URL specified")

  oBZ = bugz.bugzilla.Bugz(sBZUrl, user=sBZUser, password=sBZPasswd)
  oBZ.modify(iBugId, comment=sComment)



def get_bug_status(oBugz, iBugId):
  """
  given the bugz.bugzilla.Bugz instance and the bug id, returns the bug
  status.
  """
  oBug = oBugz.get(iBugId)
  if oBug is None:
    return None
  return oBug.getroot().find("bug/bug_status").text


def notify_and_exit(sMsg):
  """
  notifies the error and exits.
  """
  print """

======================================================================
Cannot accept commit.

%s

======================================================================

""" % (sMsg,)
  sys.exit(1)

