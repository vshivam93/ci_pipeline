import os, paramiko, io, base64, sys
from colorama import init, Fore, Style
init(convert=True)

from cmn_readConfig import readConfig
from cmn_botlog import logging
from cmn_checkServerStatus import checkStat
from st201_checkSt2LogPath import checkLogPath
from st202_fetchLogFiles import fetchFiles

def decode(data):
    inp = data.encode("ascii")
    data = base64.b64decode(inp)
    op = data.decode("ascii")
    return str(op)
    
def getConnection(IP,username,password):
    try:
        SSH = paramiko.SSHClient()
        SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        SSH.connect(port=22, hostname=IP, username=username, password=password)
        return SSH
    except Exception as err:
        return f"False # {str(err)}"

def main(corrID, ssh_user, ssh_pass):
    resDict = {'alertLogPath': "", 'incLogPath': ""}
    try:
        if os.path.exists(os.path.join(os.getcwd(), "config.ini")):
            configFile_enc = os.path.join(os.getcwd(), "config.ini")
            configFile_enc = open(configFile_enc, 'r').read()
            configFile_dec = io.StringIO()
            configFile_dec.write(decode(configFile_enc))
            configFile_dec.seek(0)

            config = readConfig(configFile_dec)
        else:
            logging("config.ini file not present..Kindly Check !!", "WARN")
            exit(0)
        
        config = config['ST2']

        for st2IP in [config['st2Server1'], config['st2Server2']]:
            # Check Server Status
            serverStat = checkStat(st2IP)
            if serverStat == "True":
                # Create an SSH connection
                ssh = getConnection(st2IP, ssh_user, ssh_pass)
                if 'False' not in str(ssh):
                    for pathToCheck in resDict:
                        # Validate Log Path Existence
                        res = checkLogPath(ssh, config[pathToCheck], f"{corrID}_.txt")
                        if res != '':
                            # Fetch Log File contents and save it locally
                            logFileContent = fetchFiles(ssh, config[pathToCheck], f"{corrID}_.txt")
                            if logFileContent != '':
                                if 'alert' in pathToCheck:
                                    artFilePath = os.path.join(os.path.join(os.getcwd(), "Artifacts"), f"ST2\Alert_{corrID}.txt")
                                else:
                                    artFilePath = os.path.join(os.path.join(os.getcwd(), "Artifacts"), f"ST2\Inc_{corrID}.txt")
                                print(logFileContent, file=open(artFilePath, 'w'))
                                print(f"{Fore.GREEN}Log File from {pathToCheck} fetched successfully..{Style.RESET_ALL}")
                                logging(f"Log File from {pathToCheck} fetched successfully..", "INFO")
                                resDict[pathToCheck] = True
                            else:
                                print(f"{Fore.RED}Unable to fetch Log File Content from {st2IP}..{Style.RESET_ALL}")
                                logging(f"Unable to fetch Log File Content from {st2IP}..", "WARN")
                                resDict[pathToCheck] = False
                        else:
                            print(f"{Fore.RED}Log Path for {pathToCheck} does not exist on {st2IP}..{Style.RESET_ALL}")
                            resDict[pathToCheck] = False
                            logging(f"Log Path for {pathToCheck} does not exist on {st2IP}..", "WARN")
                    ssh.close()

                    if True in [resDict['alertLogPath'], resDict['incLogPath']]:
                        break
                else:
                    print(f"{Fore.RED}Failure with ssh connection to {st2IP}: {ssh}{Style.RESET_ALL}")
                    logging(f"Failure with ssh connection to {st2IP}: {ssh}", "ERROR")
            elif serverStat == "False":
                print(f"{Fore.RED}ST2 Server {st2IP} is unreachable..Kindly Check..!!{Style.RESET_ALL}")
                logging(f"ST2 Server {st2IP} is unreachable..Kindly Check..!!", "WARN")
            else:
                logging(serverStat, "ERROR")
    except Exception as e:
        # print(f"{Fore.RED}Func | f1: ERROR occurred: {e}{Style.RESET_ALL}")
        logging(f"Func | f1: ERROR occurred: {e}", "ERROR")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging(f"{exc_type}, {fname}, {exc_tb.tb_lineno}", "WARN")
    finally:
        return resDict['alertLogPath'], resDict['incLogPath']
