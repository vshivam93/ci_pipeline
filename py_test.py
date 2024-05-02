import sys, os, io, base64, getpass
from datetime import datetime, timedelta
from prettytable import PrettyTable
from colorama import init, Fore, Style
init(convert=True)

# ---- Appending MasterBot, Functionalities and MicroBots path to SYSPATH ----
sys.path.append(os.path.join(os.getcwd(), "MasterBot"))
sys.path.append(os.path.join(os.getcwd(), "Functionalities"))
sys.path.append(os.path.join(os.getcwd(), "MicroBots"))

# ---- Importing Functionality Bots ----
# from cmn_fetchFAQ import fetchFAQ
import f1_st2HealthCheck as f1
import f2_dbHealthCheck as f2
import f3_mfooHealthCheck as f3
import f4_rasHealthCheck as f4

# ------ Importing Common Bots ------
from cmn_readConfig import readConfig
from cmn_botlog import logging

# ---- Importing Bots specific to MasterBot ----
from mb_getIncidentCount import getIncidentCount
from mb_getSnowData import getSnowData
from mb_checkSnowStatus import checkSnowStatus


def getRAS(workNote):
    rasServer = ""
    for line in workNote.split('\n'):
        if "Successfully triggered the Master Bot placed on RAS server.##### Success" in line.strip():
            temp = line.split("Success")[2].strip()
            if rasServer != temp:
                rasServer = temp.strip()
            break
        elif "Ras precheck Successfull on RAS" in line:
            temp = line.split(" : ")[0].split(" ")[-1]
            if rasServer != temp:
                rasServer = temp.strip()
            break
        elif "Precheck success: RAS:" in line and "Precheck success: RAS:localhost" not in line:
            temp = line.split("Precheck success: RAS:")[1]
            temp = temp.split(' ')[0]
            if rasServer != temp:
                rasServer = temp.strip()
        elif "Precheck success for RAS:" in line and "Precheck success for RAS:localhost" not in line:
            temp = line.split("Precheck success for RAS:")[1]
            temp = temp.split(' ')[0]
            if rasServer != temp:
                rasServer = temp.strip('True').strip()
    return rasServer

def masterBotMain(corrID, rasServer, ssh_user, ssh_pass):
    colorCodeDict = {True: 'lightgreen', False: 'red'}
    statusDict = {True: 'Present', False: 'Absent'}

    # -------- HTML Report components ############# --------
    header = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AiMili0 Autoheal Troubleshooting</title>
        <link rel = "icon" href =  "../HTML_Files/Capgemini_Icon.ico" type = "image/x-icon">
        <style>
            body, html {
                height: 100%;
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                }
            * {
                box-sizing: border-box;
            }
            .bg-image {
                background-image: url("../HTML_Files/Capgemini_Logo.png");
                background-repeat: no-repeat;
                background-position: 130% 10%;
                background-size: 65%;

                /* Full height */
                height: 100%;
                
                opacity: 50%;
            }

            /* Position text in the middle of the page/image */
            .bg-text {
                background-color: rgb(0,0,0); /* Fallback color */
                background-color: rgba(0,0,0, 0.05); /* Black w/opacity/see-through */
            
                font-weight: bold;
                border: 3px solid #f2f2f2;
                position: absolute;
                top: 48%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 2;
                width: 98%;
                padding: 10px;
                backdrop-filter: blur(5px);
            }
            h3 {
                text-align: center;
                color: #0070ad;
            }
            table, th, td {
                border: 2px solid black;
                border-collapse: collapse;
                padding-top: 2px;
                padding-bottom: 2px;
                padding-left: 5px;
                padding-right: 5px;
            }
            th {font-size: 14px;}
            td {font-size: 12px;}
            img {
                position: absolute;
                right: 10px;
                bottom: 0px;
              }
        </style>
    </head>
    <body>
        <div class="bg-image"></div>
        <div class="bg-text">
            <h3>AiMili0 Autoheal Troubleshooting Result</h3>
    """

    footer = """
            </div>
        </div>
    </body>
    </html>
    """

    if incNo != "":
        corrIdComponent = f"""
            <p><b>Correlation ID analyzed:</b> {corrID} || <b>Incident Number analyzed:</b> {incNo}</p>
            <div>
        """
    else:
        corrIdComponent = f"""
                <p><b>Correlation ID analysed:</b> {corrID}</p>
                <div>
        """
    # ------------------------------------------------------

    # ----- Calling Stackstorm functionality Bot and capture response -----
    st2AlertRes, st2IncRes = f1.main(corrID, ssh_user, ssh_pass)

    alertArtRes = f"""<td><a href="../Artifacts/ST2/Alert_{corrID}.txt" target=”_blank”>{corrID}.txt</a></td>""" if st2AlertRes is True else f"""<td></td>"""
    incArtRes = f"""<td><a href="../Artifacts/ST2/Inc_{corrID}.txt" target=”_blank”>{corrID}.txt</a></td>""" if st2IncRes is True else f"""<td></td>"""

    st2HcTable = f"""
                <h5>1. StackStorm WebHook Log Availability Check</h5>
                <table>
                    <tbody>
                    <tr>
                        <th>Checks</th>
                        <th>Location/Path</th>
                        <th>Status</th>
                        <th>Artifact</th>
                    </tr>
                    <tr>
                        <td>Alert API Log File Presence</td>
                        <td>/scripts/autoheal/AH_Alert_API_Internal_Dump_logs/WebHookLogs/AAH/AlertAPI</td>
                        <td style="background-color:{colorCodeDict[st2AlertRes]};">{statusDict[st2AlertRes]}</td>
                        {alertArtRes}
                    </tr>
                    <tr>
                        <td>Incident API Log File Presence</td>
                        <td>/scripts/autoheal/AH_IncidentUpdateAPI_InternalValidator_pathSP/WebHookLogs/AAH_ST2/IncidentUpdateAPI_Insert</td>
                        <td style="background-color:{colorCodeDict[st2IncRes]};">{statusDict[st2IncRes]}</td>
                        {incArtRes}
                    </tr>
                    </tbody>
                </table>
        """

    # st2HcFAQ = ""
    # if st2AlertRes is False or st2IncRes is False:
    #     if st2AlertRes is False and st2IncRes is False:
    #         res = fetchFAQ("Alert API Log File Presence", "Incident API Log File Presence")
    #     elif st2AlertRes is False:
    #         res = fetchFAQ("Alert API Log File Presence")
    #     elif st2IncRes is False:
    #         res = fetchFAQ("Incident API Log File Presence")
        
    #     faqRes = ""
    #     for line in res:
    #         faqRes = faqRes + f"<li>{line}</li>\n"

    #     st2HcFAQ = f"""
    #         <p>
    #             <b>Possible known issues to check:</b><br>
    #             Either of the below could be the reason for the above status being marked as <b style="color:red;">RED</b>:
    #             <ol>
    #                 {faqRes}
    #             </ol>
    #         </p>
    #     """
    # ---------------------------------------------------------------------

    # ----- Calling DB functionality Bot and capture response -----
    
    dbRes, runID = f2.main(corrID)

    dbArtRes = f"""<td><a href="../Artifacts/DB/DB_{corrID}.txt" target=”_blank”>{corrID}.txt</a></td>""" if dbRes is True else f"""<td></td>"""

    dbHcTable = f"""
                <h5>2. Database Records Availability Check</h5>
                <table>
                    <tbody>
                    <tr>
                        <th>Checks</th>
                        <th>Location/Path</th>
                        <th>Status</th>
                        <th>Artifact</th>
                    </tr>
                    <tr>
                        <td>DB Record Presence</td>
                        <td>Database: OO_Automation || Table Name: AHF_AlertAPI</td>
                        <td style="background-color:{colorCodeDict[dbRes]};">{statusDict[dbRes]}</td>
                        {dbArtRes}
                    </tr>
                    </tbody>
                </table>
        """
    # -------------------------------------------------------------

    # ----- Calling MFOO functionality Bot and capture response -----
    mfooPollerRes, mfooValidatorRes, mfooStepsRes = f3.main(corrID, runID)

    mfooPollerArtRes = f"""<td><a href="../Artifacts/Poller_Validator/Poller_{corrID}.txt" target=”_blank”>{corrID}.txt</a></td>""" if mfooPollerRes is True else f"""<td></td>"""
    mfooValidatorArtRes = f"""<td><a href="../Artifacts/Poller_Validator/Validator_{corrID}.txt" target=”_blank”>{corrID}.txt</a></td>""" if mfooValidatorRes is True else f"""<td></td>"""
    mfooStepsArtRes = f"""<td><a href="../Artifacts/MFOO_Step_Logs/MFOO_{corrID}.xml" target=”_blank”>{corrID}.xml</a></td>""" if mfooStepsRes is True else f"""<td></td>"""

    mfooHcTable = f"""
                <h5>3. MFOO Logs Availability Check</h5>
                <table>
                    <tbody>
                    <tr>
                        <th>Checks</th>
                        <th>Location/Path</th>
                        <th>Status</th>
                        <th>Artifact</th>
                    </tr>
                    <tr>
                        <td>Poller Log Presence</td>
                        <td>C:\Automation\Aimilio\Autoheal\Validator\pollerLogs</td>
                        <td style="background-color:{colorCodeDict[mfooPollerRes]};">{statusDict[mfooPollerRes]}</td>
                        {mfooPollerArtRes}
                    </tr>
                    <tr>
                        <td>Validator Log Presence</td>
                        <td>C:\Automation\Aimilio\Autoheal\Validator\WebHookLogs\AAH\IncidentUpdateAPI_Insert</td>
                        <td style="background-color:{colorCodeDict[mfooValidatorRes]};">{statusDict[mfooValidatorRes]}</td>
                        {mfooValidatorArtRes}
                    </tr>
                    <tr>
                        <td>MFOO Steps Log Presence</td>
                        <td>Location: MFOO Central || Run ID: {runID}</td>
                        <td style="background-color:{colorCodeDict[mfooStepsRes]};">{statusDict[mfooStepsRes]}</td>
                        {mfooStepsArtRes}
                    </tr>
                    </tbody>
                </table>
        """
    # ---------------------------------------------------------------

    # ----- Calling RAS functionality Bot and capture response -----
    rasLogRes = f4.main(corrID, rasServer)

    rasLogArtRes = f"""<td><a href="../Artifacts/RAS/RAS_{corrID}.txt" target=”_blank”>{corrID}.txt</a></td>""" if rasLogRes is True else f"""<td></td>"""
    
    rasHcTable = f"""
                <h5>3. RAS Log Availability Check</h5>
                <table>
                    <tbody>
                    <tr>
                        <th>Checks</th>
                        <th>Location/Path</th>
                        <th>Status</th>
                        <th>Artifact</th>
                    </tr>
                    <tr>
                        <td>RAS Log Presence</td>
                        <td>RAS Server: {rasServer}</td>
                        <td style="background-color:{colorCodeDict[rasLogRes]};">{statusDict[rasLogRes]}</td>
                        {rasLogArtRes}
                    </tr>
                    </tbody>
                </table>
        """
    # ---------------------------------------------------------------

    # --------- Combining the outputs into one HTML Report ----------
    output =f"""
    {header}
                <hr>
    {corrIdComponent}
    {st2HcTable}
                <hr>
    {dbHcTable}
                <hr>
    {mfooHcTable}
                <hr>
    {rasHcTable}
    # {footer}
    """
    htmlFilePath = os.path.join(os.getcwd(), f"Reports/output_{corrID}.html")

    print(output, file=open(htmlFilePath, 'w'))
    print(f"{Fore.GREEN}\nReport has been generated successfully..{Style.RESET_ALL}")
    logging("---------------------------------------------------------------", "INFO")
    # ---------------------------------------------------------------

    # Opening the Report in the default browser on the system
    os.system(f"start {htmlFilePath}")

def decode(data):
    inp = data.encode("ascii")
    data = base64.b64decode(inp)
    op = data.decode("ascii")
    return str(op)

if __name__ == "__main__":
    # Validate and create Reports directory (if needed)
    reportPath = os.path.join(os.getcwd(), "Reports")
    if os.path.exists(reportPath) is False:
            os.makedirs(reportPath, exist_ok=True)
            logging("Reports directory created...", "INFO")
    
    # Validate and fetch config.ini file/contents
    if os.path.exists(os.path.join(os.getcwd(), "config.ini")):
        logging("Reading the config.ini contents...", "INFO")

        configFile_enc = os.path.join(os.getcwd(), "config.ini")
        configFile_enc = open(configFile_enc, 'r').read()
        configFile_dec = io.StringIO()
        configFile_dec.write(decode(configFile_enc))
        configFile_dec.seek(0)

        config = readConfig(configFile_dec)
        logging("Config.ini contents fetched successfully...", "INFO")
    else:
        print("config.ini file not present..Kindly Check !!")
        logging("config.ini file not present..Kindly Check !!", "WARN")
        exit(0)

    print('\n')
    print(f"{Fore.RED}----------------------------------------------------------------------------------{Style.RESET_ALL}")
    print(f"{Fore.BLUE}-*-*-*-*-*-*-*-*-*-*-*-*{Fore.CYAN} AiMili0 Autoheal Troubleshooting {Fore.BLUE}*-*-*-*-*-*-*-*-*-*-*-*-{Style.RESET_ALL}")
    while 1:
        opt = ""; incNo = ""; corrID = ""; snowConfig = ""
        print(f"{Fore.RED}----------------------------------------------------------------------------------{Style.RESET_ALL}")
        # ----- User input choice for Internal or External Customer -----
        while 1:
            print("\nPlease select your option from the below:")
            print(f"{Fore.CYAN}\t1.{Style.RESET_ALL} Troubleshoot for Internal Customer")
            print(f"{Fore.CYAN}\t2.{Style.RESET_ALL} Troubleshoot for External Customer")
            print(f"{Fore.CYAN}\t3.{Style.RESET_ALL} Exit")
            opt = input("Enter your option: ")
            if opt in ['1', '2', '3']:
                if opt == '3':
                    print(f"{Fore.BLUE}---------------------------------{Fore.GREEN} || Thank You || {Fore.BLUE}--------------------------------{Style.RESET_ALL}")
                    exit()
                break
            else:
                print(f"{Fore.RED}Please enter a valid option !!\n{Style.RESET_ALL}")
                continue
        
        if opt == '1':
            print(f"{Fore.RED}\n----------------------------------------------------------------------------{Style.RESET_ALL}")
            print(f"{Fore.BLUE}-*-*-*-*-*{Fore.CYAN} AiMili0 Autoheal Troubleshooting for Internal Customer {Fore.BLUE}*-*-*-*-*-{Style.RESET_ALL}")
            print(f"{Fore.RED}----------------------------------------------------------------------------{Style.RESET_ALL}")
            logging(f"Internal Customer opted..", "INFO")
            snowConfig = config['SNOW']
        elif opt == '2':
            print(f"{Fore.RED}\n---------------------------------------------------------------------------------{Style.RESET_ALL}")
            print(f"{Fore.BLUE}-----------{Fore.GREEN} Functionality for External Customers is under development {Fore.BLUE}-----------{Style.RESET_ALL}")
            print(f"{Fore.RED}---------------------------------------------------------------------------------{Style.RESET_ALL}")
            break
            # opt = ""
            # print(f"{Fore.RED}\n----------------------------------------------------------------------------{Style.RESET_ALL}")
            # print(f"{Fore.BLUE}-*-*-*-*-*{Fore.CYAN} AiMili0 Autoheal Troubleshooting for External Customer {Fore.BLUE}*-*-*-*-*-{Style.RESET_ALL}")
            # print(f"{Fore.RED}----------------------------------------------------------------------------{Style.RESET_ALL}")
            
            # if os.path.exists(os.path.join(os.getcwd(), "ext_customer_ITSM_details.ini")):
            #     extCustITSMDetails = readConfig(os.path.join(os.getcwd(), "ext_customer_ITSM_details.ini"))
            # else:
            #     print("ext_customer_ITSM_details.ini file not present..Kindly Check !!")
            #     exit(0)
            # print("Below are the External Customers who are onboarded for Troubleshooting:")
            # for index, cust in enumerate(extCustITSMDetails):
            #     print(f"\t{Fore.CYAN}{index+1}.{Style.RESET_ALL} {cust}")

            # opt = input(f"Choose option {Fore.YELLOW}(1, 2, 3...){Style.RESET_ALL} from above to continue or 'N' to restart: ")
            # if opt.lower() == 'n':
            #     continue
            # elif int(opt) <= len(extCustITSMDetails):
            #     customers = list(extCustITSMDetails.keys())
            #     snowConfig = extCustITSMDetails[customers[int(opt)-1]]
            #     print(f"\n{Fore.CYAN}Customer opted: {Style.RESET_ALL} {customers[int(opt)-1]}")
            #     logging(f"External Customer opted: {customers[int(opt)-1]}", "INFO")
            # else:
            #     print(f"{Fore.RED}Please enter a valid option !!\n{Style.RESET_ALL}")
            #     continue
        
        # ----- Check ServiceNow Status -----
        print(f"{Fore.YELLOW}Checking ServiceNow Availability. Please wait..!!{Style.RESET_ALL}")
        if checkSnowStatus(snowConfig['instanceUrl']):
            print(f"{Fore.GREEN}{snowConfig['instanceUrl']} is up and accessible...{Style.RESET_ALL}")
            logging(f"{snowConfig['instanceUrl']} is up and running...", "INFO")

            # ----- Total P3 and P4 Incident Count -----
            while 1:
                startDateInput = ""; endDateInput = ""
                expected_format="%Y-%m-%d %H:%M:%S"

                print(f"\n{Fore.BLUE}--------------------------{Fore.CYAN} Total Incident Count {Fore.BLUE}-------------------------{Style.RESET_ALL}")
                print(f"""{Fore.YELLOW}(Note: Press "ENTER" if you want to use the system's current Date & Time){Style.RESET_ALL}""")
                dateInput = input(f"Start Date & Time ({Fore.YELLOW}YYYY-MM-DD HH:MM:SS{Style.RESET_ALL}): ")
                hours = input(f"Enter the number of hours ({Fore.YELLOW}Max: 7 or -7{Style.RESET_ALL}): ")

                if dateInput == "":
                    dateInput = datetime.strftime(datetime.now(), expected_format)
                
                if -7 > int(hours) or int(hours) > 7:
                    print(f"{Fore.RED}Enter the hours between the specified range...{Style.RESET_ALL}")
                    continue
                elif hours[0] == '-':
                    startDateInput = datetime.strptime(dateInput, expected_format) + timedelta(hours=int(hours))
                    startDateInput = datetime.strftime(startDateInput, expected_format)
                    endDateInput = dateInput
                elif hours[0] != '-':
                    startDateInput = dateInput
                    endDateInput = datetime.strptime(dateInput, expected_format) + timedelta(hours=int(hours))
                    endDateInput = datetime.strftime(endDateInput, expected_format)
                
                try:
                    datetime.strptime(startDateInput, expected_format)
                    datetime.strptime(endDateInput, expected_format)
                    if datetime.strptime(startDateInput, expected_format) > datetime.strptime(endDateInput, expected_format):
                        print(f"{Fore.RED}Start Date & Time should be less than or equal to the End Date & Time..\nKindly Re-Enter..!{Style.RESET_ALL}")
                        continue
                except ValueError:
                    print(f"{Fore.RED}Enter the above values in specified format..{Style.RESET_ALL}")
                    continue
                
                print(f"{Fore.CYAN}\nStart DateTime: {Fore.GREEN}{startDateInput}{Style.RESET_ALL} | {Fore.CYAN}End DateTime: {Fore.GREEN}{endDateInput}{Style.RESET_ALL}")
                print("Calculating w.r.t. the above specified period...")
                logging(f"Start Date and Time: {startDateInput} | End Date and Time: {endDateInput}", "INFO")
                
                p3IncCount, p4IncCount = getIncidentCount(snowConfig, startDateInput, endDateInput)
                for item in [p3IncCount, p4IncCount]:
                    keys = list(item.keys())
                    if item[keys[0]] is True:
                        print(f"Total Count of {Fore.CYAN}{'P3' if 'p3' in keys[0] else 'P4'}{Style.RESET_ALL} Incidents: {Fore.GREEN}{item[keys[1]]}{Style.RESET_ALL}")
                        logging(f"Total Count of {'P3' if 'p3' in keys[0] else 'P4'} Incidents: {item[keys[1]]}", "INFO")
                    else:
                        print(f"Total Count of {Fore.CYAN}{'P3' if 'p3' in keys[0] else 'P4'}{Style.RESET_ALL} Incidents: {Fore.RED}Unable to fetch the Count..!!{Style.RESET_ALL}")
                        logging(f"Total Count of {'P3' if 'p3' in keys[0] else 'P4'} Incidents: Unable to fetch the Count..!!", "INFO")
                print(f"{Fore.BLUE}-------------------------------------------------------------------------{Style.RESET_ALL}")
                break
        
        else:
            print(f"{Fore.RED}{snowConfig['instanceUrl']} is either down or not accessible...Please Check !!{Style.RESET_ALL}")
            logging(f"{snowConfig['instanceUrl']} is either down or not accessible...Please Check !!", "ERROR")
        
        # ----- User Input choice for Troubleshooting with Inc Number or Correlation ID -----
        while 1:
            print("\nPlease select your option from the below:")
            print(f"{Fore.CYAN}\t1.{Style.RESET_ALL} Troubleshoot with Incident Number")
            print(f"{Fore.CYAN}\t2.{Style.RESET_ALL} Troubleshoot with Correlation ID")
            print(f"{Fore.CYAN}\t3.{Style.RESET_ALL} Exit")
            opt = input("Enter your option: ")
            if opt in ['1', '2', '3']:
                if opt == '3':
                    print(f"{Fore.BLUE}---------------------------------{Fore.GREEN} || Thank You || {Fore.BLUE}--------------------------------{Style.RESET_ALL}")
                    exit()
                break
            else:
                print(f"{Fore.RED}Please enter a valid option !!\n{Style.RESET_ALL}")
                continue

        if opt == '1':
            incNo = input("Enter the Incident Number: ")
        elif opt == '2':
            corrID = input("Enter the Correlation ID: ")

        if incNo != "":
            while 1:
                if incNo[-1] in ['*', '%']:
                    incNo = incNo[:-1]
                elif incNo[0] in ['*', '%']:
                    incNo = incNo[1:]
                else:
                    break

        print(f"\n{Fore.YELLOW}Input entered is: {Fore.GREEN}{incNo if incNo != '' else corrID}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Searching for possible results from ServiceNow...{Style.RESET_ALL}")
        dataList = getSnowData(snowConfig, incNo if incNo != "" else corrID, opt)

        if len(dataList) == 1:
            dataList = dataList[0]
            print(f"{Fore.GREEN}\nBelow is the Incident identified:{Style.RESET_ALL}")
            table = PrettyTable()
            table.add_row([f"{Fore.CYAN}Incident Number{Style.RESET_ALL}",      f"{Fore.YELLOW}{dataList.get('number')}{Style.RESET_ALL}"])
            table.add_row([f"{Fore.CYAN}Company{Style.RESET_ALL}",              f"{Fore.YELLOW}{dataList.get('company_name')}{Style.RESET_ALL}"])
            table.add_row([f"{Fore.CYAN}Priority{Style.RESET_ALL}",             f"{Fore.YELLOW}{dataList.get('priority')}{Style.RESET_ALL}"])
            table.add_row([f"{Fore.CYAN}Short Description{Style.RESET_ALL}",    f"{Fore.YELLOW}{dataList.get('short_description')}{Style.RESET_ALL}"])
            table.add_row([f"{Fore.CYAN}CorrelationID{Style.RESET_ALL}",        f"{Fore.YELLOW}{dataList.get('correlation_id')}{Style.RESET_ALL}"])
            table.add_row([f"{Fore.CYAN}Created{Style.RESET_ALL}",              f"{Fore.YELLOW}{dataList.get('opened_at')}{Style.RESET_ALL}"])
            
            table.header = False
            table._align['Field 1'] = 'r'
            table._align['Field 2'] = "l"

            print(table)
            # print(f"{Fore.BLUE}-----------------------------------{Style.RESET_ALL}")
            # print(f"{Fore.CYAN}Incident Number:{Style.RESET_ALL}",   dataList.get('number'))
            # print(f"{Fore.CYAN}Company:{Style.RESET_ALL}",           dataList.get('company_name'))
            # print(f"{Fore.CYAN}Priority:{Style.RESET_ALL}",          dataList.get('priority'))
            # print(f"{Fore.CYAN}Short Description:{Style.RESET_ALL}", dataList.get('short_description'))
            # print(f"{Fore.CYAN}CorrelationID:{Style.RESET_ALL}",     dataList.get('correlation_id'))
            # print(f"{Fore.CYAN}Created:{Style.RESET_ALL}",           dataList.get('opened_at'))
            # print(f"{Fore.BLUE}-----------------------------------\n{Style.RESET_ALL}")
            confirm = input(f"Enter {Fore.YELLOW}'Y'{Style.RESET_ALL} to continue with the above result or {Fore.YELLOW}'N'{Style.RESET_ALL} to restart: ")
            if confirm.lower() == 'y':
                ssh_user = input(f"{Fore.CYAN}Enter the username for StackStorm server SSH Connection:{Style.RESET_ALL} ")
                ssh_pass = getpass.getpass(f"{Fore.CYAN}Enter the Password for StackStorm server SSH Connection:{Style.RESET_ALL} ")
                
                corrID = dataList.get('correlation_id')
                print(f"{Fore.BLUE}-----------------------------------------------------------------{Style.RESET_ALL}")
                rasServer = getRAS(dataList.get('work_notes'))
                if rasServer != "":
                    print(f"{Fore.CYAN}Correlation ID:{Style.RESET_ALL} {corrID} || {Fore.CYAN}RAS:{Style.RESET_ALL} {rasServer}\n")
                    logging(f"Call MasterBot with respective Correlation ID {corrID} and RAS {rasServer}", "INFO")
                else:
                    print(f"{Fore.RED}No RAS Server found in incident workNotes...{Style.RESET_ALL} Correlation ID: {corrID}\n")
                    logging(f"No RAS Server found in incident workNotes. Hence, call MasterBot with respective Correlation ID {corrID}", "INFO")
                
                # ----- Call MasterBotMain function -----
                print(f"{Fore.YELLOW}Bot has started gathering the Data. Please wait..!!\n{Style.RESET_ALL}")
                masterBotMain(corrID, rasServer, ssh_user, ssh_pass)
                break
            elif confirm.lower() == 'n':
                print('\n')
                continue
            else:
                print(f"{Fore.RED}Invalid Response..{Style.RESET_ALL}")
                continue
        # elif len(dataList) > 1:
        #     print(f"{Fore.GREEN}Below are the Incidents identified:{Style.RESET_ALL}")
        #     print(f"{Fore.BLUE}-----------------------------------{Style.RESET_ALL}")
        #     for index, incident in enumerate(dataList):
        #         print(f"{Fore.CYAN}{index+1}.\tIncident Number:{Style.RESET_ALL}", incident.get('number'))
        #         print(f"{Fore.CYAN}\tCompany:{Style.RESET_ALL}",                   incident.get('company_name'))
        #         print(f"{Fore.CYAN}\tPriority:{Style.RESET_ALL}",                  incident.get('priority'))
        #         print(f"{Fore.CYAN}\tShort Description:{Style.RESET_ALL}",         incident.get('short_description'))
        #         print(f"{Fore.CYAN}\tCorrelationID:{Style.RESET_ALL}",             incident.get('correlation_id'))
        #         print(f"{Fore.CYAN}\tCreated:{Style.RESET_ALL}",                   incident.get('opened_at'))
        #         print(f"{Fore.BLUE}-----------------------------------{Style.RESET_ALL}")
            
        #     print('\n')
        #     confirm = input(f"Choose your option {Fore.YELLOW}(1, 2, 3...){Style.RESET_ALL} from the above result to continue or 'N' to restart: ")
        #     if confirm.lower() == 'n':
        #         print('\n')
        #         continue
        #     elif confirm.lower() == 'y':
        #         corrID = dataList[int(confirm)-1].get('correlation_id')
        #         print(f"{Fore.BLUE}-----------------------------------------------------------------{Style.RESET_ALL}")
        #         print("Correlation ID to work with: ",corrID)
        #         rasServer = getRAS(dataList[int(confirm)-1].get('work_notes'))
        #         if rasServer != "":
        #             print(f"{Fore.CYAN}Correlation ID:{Style.RESET_ALL} {corrID} || {Fore.CYAN}RAS:{Style.RESET_ALL} {rasServer}\n")
        #             logging(f"Call MasterBot with respective Correlation ID {corrID} and RAS {rasServer}", "INFO")
        #         else:
        #             print(f"{Fore.RED}No RAS Server found in incident workNotes..{Style.RESET_ALL} Correlation ID: {corrID}\n")
        #             logging(f"No RAS Server found in incident workNotes. Hence, call MasterBot with respective Correlation ID {corrID}", "INFO")
                
        #         # ----- Call MasterBotMain function -----
        #         print(f"{Fore.YELLOW}Bot has started gathering the Data. Please wait..!!\n{Style.RESET_ALL}")
        #         masterBotMain(corrID, rasServer)
        #         break
        #     else:
        #         print(f"{Fore.RED}Invalid Response..{Style.RESET_ALL}")
        #         continue
        else:
            print(f"{Fore.RED}No Data found for {incNo if incNo != '' else corrID}{Style.RESET_ALL}")
