import sys
from socket import *
import select
import threading
from time import sleep, localtime,strftime

def getTime():
    t = localtime()
    current_time = strftime("%H:%M:%S", t)
    return current_time


def receive_data(clientPort,restart_event):

    global info
    while info["QUIT"]==False:
        #if info["active"]==True:
        listenSocket = socket(AF_INET, SOCK_DGRAM)
        
        listenSocket.bind(('', clientPort))

        ##print("waiting")

        info["listenSocket"]=listenSocket
        modifiedMessage, fromAddress = listenSocket.recvfrom(2048)
        # listenSocket.close()
        #print(modifiedMessage.decode())

        if info["QUIT"]==True:
            listenSocket.close()
            return
        

        response=eval(modifiedMessage.decode())

        isTable=(response["type"]=="table_update")
        isMsg=(response["type"]=="msg" )
        isOfflineMessages=(response["type"]=="offline_messages")
        isGC=(response["type"]=="GC")
        isACK=(response["type"]=="ack")
        isStatus=(response["type"]=="status_check")
        isError=(response["type"]=="error")
        
        if isError:
            print(">>> "+response["message"])
            info["resend"]=True
            
            #print()
            #print("Table:"+str(info["table"]))
            #print()
            listenSocket.close()
            restart_event.set()


        elif isACK:
            #print("was_ack from "+response["from"])

            listenSocket.close()
            restart_event.set()
            

        elif isStatus:
            #print("status_checkkkkk")
            sending=dict()
            sending["type"]="status_confirm"
            sending["from"]=info["clientName"]

            sendackSocket = socket(AF_INET, SOCK_DGRAM)
            sendackSocket.sendto(str(sending).encode(),(info["serverIP"], info["serverPort"]))
            sendackSocket.close()

            listenSocket.close()
            restart_event.set()


        elif isTable:
            info["table"]=response["table"]
            #print()
            #print("Table:"+str(info["table"]))
            #print
            listenSocket.close()
            restart_event.set()



        elif isMsg:

            #sendACK
            if info["active"]==True:
                #print()
                if (response["name_from"]!=None and response["name_from"] in info["table"].keys()):

                    sending=dict()
                    sending["type"]="ack"
                    sending["from"]=info["clientName"]

                    toackClientIP=info["table"][response["name_from"]][1]
                    toackClientPort=info["table"][response["name_from"]][2]


                    sendackSocket = socket(AF_INET, SOCK_DGRAM)
                    sendackSocket.sendto(str(sending).encode(),(toackClientIP, toackClientPort))
                    sendackSocket.close()

                    #print(">>> "+response["name_from"]+": "+response["msg"])
                    print(response["name_from"]+": "+response["msg"])
                    #print(">>> "+response["msg"])
                    #print(">>> ",end=" ")

                    # listenSocket.close()
                    # restart_event.set()

                    #print()

                else:
                    sending=dict()
                    sending["type"]="ack"
                    sending["from"]=info["clientName"]
                    sendackSocket = socket(AF_INET, SOCK_DGRAM)
                    sendackSocket.sendto(str(sending).encode(),(info["serverIP"], info["serverPort"]))
                    sendackSocket.close()

                    #print(">>> "+response["msg"])
                    print(response["msg"])
                    print(">>> ",end=" ")
                    # listenSocket.close()
                    # restart_event.set()
            listenSocket.close()
            restart_event.set()
            
        
        elif isOfflineMessages:
            #print("/yoyoyo")
            sending=dict()
            sending["type"]="ack"
            sending["from"]=info["clientName"]


            sendackSocket = socket(AF_INET, SOCK_DGRAM)
            sendackSocket.sendto(str(sending).encode(),(info["serverIP"], info["serverPort"]))
            sendackSocket.close()



            


            if(len(response["offline_messages"])>0):
            
                print(">>> [You have offline messages:]")
                offline_messages=response["offline_messages"]
                for x in offline_messages:
                    
                    name, timestamp, message, fromGC=x
                    if fromGC==False:
                        if name!=None:
                            print(">>> "+ name +": "+timestamp +" "+message )
                        else:
                            print(">>> "+message)

                    else:
                        print(">>> Group Chat "+ name +": "+timestamp +" "+message )
            listenSocket.close()
            restart_event.set()


        elif isGC:
            

            sending=dict()
            sending["type"]="ack"
            sending["from"]=info["clientName"]
            sendackSocket = socket(AF_INET, SOCK_DGRAM)
            sendackSocket.sendto(str(sending).encode(),(info["serverIP"], info["serverPort"]))
            sendackSocket.close()

            print(">>> Group Chat "+ response["name"] +": " +" "+response["message"] )
            listenSocket.close()
            restart_event.set()
            
 
 
def input_command(client_name, restart_event):
    global info
    
    while info["QUIT"]==False:
        print(">>> ",end="")
        client_input=input()
        if client_input:
            client_input=client_input.split(' ')

            if info["active"]==True:
                valid_commands={"send","send_all","dereg"}
            else:
                valid_commands={"reg"}

            isSend=(client_input[0]=="send")
            isDereg=(client_input[0]=="dereg")
            isReg=(client_input[0]=="reg")
            isGC=(client_input[0]=="send_all")
            #isOL=client_input[0]=="send_ol"
            isOL=False
            isSend=(client_input[0]=="send")


            isInvalid=(client_input[0] not in valid_commands)
            
            if isInvalid:
                print(">>> [Invalid command]")
                restart_event.set()



            elif isSend:
                if(len(client_input)>2 and client_input[1] in info["table"].keys()):
                    
                    #info["resend"]=False




                    name_to=client_input[1]
                    message=" ".join(client_input[2:])

                    ##TODO add arg# check
                    ##TODO check name in table







                    #SEND OFFLINE
                    if info["table"][name_to][3]==False:
                        #print(">>> [Receiver Inactive.]")
                        #send OL message to server
                        #print("sending OL ")
                        toServer=dict()
                        toServer["timestamp"]=getTime()
                        toServer["type"]="to_offline"
                        toServer["name_to"]=name_to
                        toServer["name_from"]=client_name

                        toServer["message"]=message
                        listenSocket=info['listenSocket']

                        tries=0
                        got_ACK=False

                        ###SEND SERVER

                        clientregSocket = socket(AF_INET, SOCK_DGRAM)
                        clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                        clientregSocket.close()

                        listenSocket=info['listenSocket']
                        listenSocket.setblocking(0)



                        ready = select.select([listenSocket], [], [], 0.1)

                        while(got_ACK==False and tries<5):
                            
                        

                    
                            if ready[0]:
                                #print("received")
                                got_ACK=True
                                sleep(.1)
                            else:
                                
                                #print(">>> [No ACK from server trying again]")

                                clientregSocket = socket(AF_INET, SOCK_DGRAM)
                                clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                                clientregSocket.close()
                            tries+=1


                        if(got_ACK==False):
                            print(">>> [Server not responding]")
                            print(">>> [Exiting]")
                            info["QUIT"]=True

                        else:
                            
                            #print(">>> [Offline Message sent at "+toServer["timestamp"]+" received by the server and saved.]")


                            if info["resend"]==False:
                                print(">>> [Offline Message sent at "+toServer["timestamp"]+" received by the server and saved.]")
                            else :
                                name_to=client_input[1]
                                toClientIP=info["table"][name_to][1]
                                toClientPort=info["table"][name_to][2]
                                response=dict()
                                response["type"]="msg"
                                response["msg"]=" ".join(client_input[2:])
                                response["name_from"]=info["clientName"]



                                clientregSocket = socket(AF_INET, SOCK_DGRAM)
                                clientregSocket.sendto(str(response).encode(),(toClientIP, toClientPort))
                                clientregSocket.close()
                                info["resend"]=False
                            # clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                            # clientregSocket.close()
                            # print("message sent to server")



                        # clientregSocket = socket(AF_INET, SOCK_DGRAM)
                        # clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))

                        # clientregSocket.close()
                        # print("message sent to server")



                    else:
                        #TRY SEND TO CLIENT
                        #print("sending message to "+str(name_to)+""+str(info["table"][name_to]))
                        toClientIP=info["table"][name_to][1]
                        toClientPort=info["table"][name_to][2]
                        response=dict()
                        response["type"]="msg"
                        response["msg"]=message
                        response["name_from"]=client_name



                        clientregSocket = socket(AF_INET, SOCK_DGRAM)
                        clientregSocket.sendto(str(response).encode(),(toClientIP, toClientPort))
                        clientregSocket.close()

                        listenSocket=info['listenSocket']

                        listenSocket.setblocking(0)

                        ready = select.select([listenSocket], [], [], 0.1)
                        if ready[0]:
                            ##SEND SUCCESSFUL
                            print(">>> [Message received by "+name_to+".]")


                        else:
                            ##NOT SENT, TRY SERVER

                            print(">>> [No ACK from "+name_to+", message sent to server.]")
                            #send OL message to server
                            #print("sending OL ")
                            toServer=dict()
                            toServer["timestamp"]=getTime()
                            toServer["type"]="to_offline"
                            toServer["name_to"]=name_to
                            toServer["name_from"]=client_name

                            toServer["message"]=message


                            clientregSocket = socket(AF_INET, SOCK_DGRAM)
                            tries=0

                            got_ACK=False
                            while(got_ACK==False and tries<5):

                                listenSocket=info['listenSocket']
                                listenSocket.setblocking(0)
                                ready = select.select([listenSocket], [], [], 0.1)

                        
                                if ready[0]:
                                    #print("received")
                                    got_ACK=True
                                    sleep(.1)
                                else:
                                    
                                    #print(">>> [No ACK from server trying again]")

                                    clientregSocket = socket(AF_INET, SOCK_DGRAM)
                                    clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                                    clientregSocket.close()
                                tries+=1

                            if(got_ACK==False):
                                print(">>> [Server not responding]")
                                print(">>> [Exiting]")
                                info["QUIT"]=True

                            else:
                                
                                # print(">>> [Offline Message sent at "+toServer["timestamp"]+" received by the server and saved.]")

                                
                                if info["resend"]==False:
                                    print(">>> [Offline Message sent at "+toServer["timestamp"]+" received by the server and saved.]")
                                else :
                                    name_to=client_input[1]
                                    toClientIP=info["table"][name_to][1]
                                    toClientPort=info["table"][name_to][2]
                                    response=dict()
                                    response["type"]="msg"
                                    response["msg"]=" ".join(client_input[2:])
                                    response["name_from"]=info["clientName"]



                                    clientregSocket = socket(AF_INET, SOCK_DGRAM)
                                    clientregSocket.sendto(str(response).encode(),(toClientIP, toClientPort))
                                    clientregSocket.close()
                                    info["resend"]=False

                            # clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                            # clientregSocket.close()
                            # print("message sent to server")




                        #print("message: "+str(message))
                else:
                    #print
                    if (name not in info["table"].keys()):
                        print(">>> [Name not found]")
                        #restart_event.set()
                    else:
                        print("[Message has no length]")
                restart_event.set()


            elif isDereg:


                info["active"]=False
                toServer=dict()
                toServer["type"]="dereg"
                toServer["name"]=client_name
                
                clientregSocket = socket(AF_INET, SOCK_DGRAM)
                clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                clientregSocket.close()


                got_ACK=False
                tries=0
                while(got_ACK==False and tries<5):

                    listenSocket=info['listenSocket']
                    listenSocket.setblocking(0)
                    ready = select.select([listenSocket], [], [], 0.1)

            
                    if ready[0]:
                        #print("received")
                        got_ACK=True
                    else:
                        
                        #print(">>> [No ACK from server trying again]")

                        clientregSocket = socket(AF_INET, SOCK_DGRAM)
                        clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                        clientregSocket.close()
                    tries+=1

                if(got_ACK==False):
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    info["QUIT"]=True

                else:
                    print(">>> [You are Offline. Bye.]")
                restart_event.set()
                #print()


            elif isReg:
                info["active"]=True
                #restart_event.set()
                # receive_thread = threading.Thread(target=receive_data, args=(info["clientPort"],info["serverIP"],info["serverPort"], restart_event))
                # receive_thread.start()
                toServer=dict()
                toServer["type"]="reg"
                toServer["name"]=client_name
                
                clientregSocket = socket(AF_INET, SOCK_DGRAM)
                clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))

                clientregSocket.close()

                print(">>> [RegSent]")



                restart_event.set()
                #print()
            elif isGC:
                if len(client_input)>1:
                    message=" ".join(client_input[1:])
                    ##TODO add arg# check
                    ##TODO check name in table
                    #print("sending GC ")
                    toServer=dict()
                    toServer["type"]="GC"
                    toServer["message"]=message
                    toServer["name"]=client_name
                    clientregSocket = socket(AF_INET, SOCK_DGRAM)

                    listenSocket=info['listenSocket']
                    listenSocket.setblocking(0)

                    clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                    clientregSocket.close()




                    ready = select.select([listenSocket], [], [], 0.1)
                    got_ACK=False
                    tries=0
                    while(got_ACK==False and tries<5):
                        
                        if ready[0]:
                            #print("received")
                            got_ACK=True
                        else:
                            
                            #print(">>> [No ACK from server trying again]")

                            clientregSocket = socket(AF_INET, SOCK_DGRAM)
                            clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                            clientregSocket.close()
                        tries+=1


                    if(got_ACK==False):
                        print(">>> [Server not responding]")
                        print(">>> [Exiting]")
                        info["QUIT"]=True

                    else:
                        
                        print(">>> [Group Message received by Server.]")






                    # #input("here2")
                    # clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                    # ##Wait for Acks
                    # clientregSocket.close()
                    # print("message: "+str(message))
                else:
                    print("invalid command")
                restart_event.set()
            elif isOL:
                if len(client_input)>2:


                    print("sending OL ")
                    toServer=dict()
                    toServer["timestamp"]=getTime()
                    toServer["type"]="to_offline"
                    toServer["name_to"]=client_input[1]
                    toServer["name_from"]=info["clientName"]

                    toServer["message"]=" ".join(client_input[2:])


                    clientregSocket = socket(AF_INET, SOCK_DGRAM)
                    tries=0

                    got_ACK=False
                    while(got_ACK==False and tries<5):

                        listenSocket=info['listenSocket']
                        listenSocket.setblocking(0)
                        ready = select.select([listenSocket], [], [], 0.1)

                
                        if ready[0]:
                            #print("received")
                            got_ACK=True
                            sleep(.1)
                        else:
                            
                            print(">>> [No ACK from server trying again]")

                            clientregSocket = socket(AF_INET, SOCK_DGRAM)
                            clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                            clientregSocket.close()
                        tries+=1

                    if(got_ACK==False):
                        print(">>> [Server not responding]")
                        print(">>> [Exiting]")
                        info["QUIT"]=True

                    else:
                        # if info["resend"]==True:
                        #     clientregSocket = socket(AF_INET, SOCK_DGRAM)
                        #     clientregSocket.sendto(str(toServer).encode(),(info["serverIP"], info["serverPort"]))
                        #     clientregSocket.close()
                        
                        if info["resend"]==False:
                            print(">>> [Offline Message sent at "+toServer["timestamp"]+" received by the server and saved.]")
                        else :
                            name_to=client_input[1]
                            toClientIP=info["table"][name_to][1]
                            toClientPort=info["table"][name_to][2]
                            response=dict()
                            response["type"]="msg"
                            response["msg"]=" ".join(client_input[2:])
                            response["name_from"]=info["clientName"]



                            clientregSocket = socket(AF_INET, SOCK_DGRAM)
                            clientregSocket.sendto(str(response).encode(),(toClientIP, toClientPort))
                            clientregSocket.close()
                            info["resend"]=False

                            








                else:
                    print("invalid command")
                restart_event.set()

        #restart_event.set()


if __name__ == "__main__":
    mode=sys.argv[1]
    if mode=="-s":
        if len(sys.argv)==3:
            
            port=int(sys.argv[2])
            if ((port<1024) or (port>65535)):
                print("Invalid Listening Port")
                # input()
            else:
                offline_messages=dict()
                seen=set()
                #ports_seen=set()
                table=dict()
                while True:
                    serverPort =port
                    
                    serverSocket = socket(AF_INET, SOCK_DGRAM)
                    serverSocket.bind(('', serverPort))
                    
                    package, clientAddress = serverSocket.recvfrom(2048)
                    
                    package=eval(package.decode())
                    
                    if package["type"]=="freg":
                        message=package["message"]
                        #input()
                        clientName=message[0]
                        clientPort=int(message[1])
                        clientIP=clientAddress[0]

                        if clientName not in seen :
                            #clientName=message[0]
                            seen.add(clientName)
                            
                            
        
                            clientStatus=True
                            #input("here3")
                           
                            
                            table[clientName]=(clientName,clientIP,clientPort,clientStatus)
                            
                            offline_messages[clientName]=[]
                            print(">>> [Client table updated.]")
                            print(table)
                            
                        
                        
                            response = dict()
                            response["type"]="conf_reg"
                            response["table"]=table

                            broadcast=dict()
                            broadcast["type"]="table_update"
                            broadcast["table"]=table
                            for key in table.keys():
                                if table[key][3]==True and key!=clientName:
                                    serverSocket.sendto(str(broadcast).encode(),(table[key][1],table[key][2]))

                            serverSocket.sendto(str(response).encode(),(clientIP,clientPort))
                            serverSocket.close()


                        else:
                           #print("Name Collision")
                            response=dict()
                            response["type"]="no_reg"

                            #modifiedMessage = str(response)
                            serverSocket.sendto(str(response).encode(),(clientIP,clientPort))
                            serverSocket.close()

                    
                    
                    elif package["type"]=="dereg":
                        # print("AHINEX")
                        # print(table[package["name"]][3])
                        #input()
                        entry=list(table[package["name"]])
                        new_entry=entry
                        new_entry[3]=False

                        table[package["name"]]=tuple(new_entry)
                       # input("past")


                        print(">>> [Client table updated.]")
                        print(table)
                        broadcast=dict()
                        broadcast["type"]="table_update"
                        broadcast["table"]=table
                        #input("inex2")
                        for key in table.keys():
                            if table[key][3]==True:

                                serverSocket.sendto(str(broadcast).encode(),(table[key][1],table[key][2]))
                            
                        serverSocket.close()

                        sending=dict()
                        sending["type"]="ack"
                        sending["from"]="server"

                        toackClientIP=table[package["name"]][1]
                        toackClientPort=table[package["name"]][2]

                        serverSocket = socket(AF_INET, SOCK_DGRAM)
                        serverSocket.bind(('', serverPort))
                        serverSocket.sendto(str(sending).encode(),(toackClientIP,toackClientPort))
                        serverSocket.close()



                    elif package["type"]=="reg":
                        
                        
                        entry=list(table[package["name"]])
                        new_entry=entry
                        new_entry[3]=True

                        table[package["name"]]=tuple(new_entry)
                        print(">>> [Client table updated.]")
                       

                        


                        broadcast=dict()
                        broadcast["type"]="table_update"
                        broadcast["table"]=table
                        #print(offline_messages)
                        #print(len(offline_messages[package["name"]]))
                        print(table)
                        #serverSocket.close()
                        # serverSocket = socket(AF_INET, SOCK_DGRAM)
                        # serverSocket.bind(('', serverPort))
                        # serverSocket.sendto(str(broadcast).encode(),(table[key][1],table[key][2]))
                                

                        for key in table.keys():
                            if (table[key][3]==True) or (key==package["name"]):
                                serverSocket = socket(AF_INET, SOCK_DGRAM)
                                serverSocket.bind(('', serverPort))
                                serverSocket.sendto(str(broadcast).encode(),(table[key][1],table[key][2]))
                                serverSocket.close()
                        sleep(.1)
                                # serverSocket = socket(AF_INET, SOCK_DGRAM)
                                # serverSocket.bind(('', serverPort))
                                # serverSocket.sendto(str(broadcast).encode(),(table[key][1],table[key][2]))
                                # serverSocket.close()
                    




                        response=dict()
                        response["type"]="offline_messages"
                        response["offline_messages"]=offline_messages[package["name"]]
                        #serverSocket.close()
                        serverSocket = socket(AF_INET, SOCK_DGRAM)
                        serverSocket.bind(('', serverPort))
                        serverSocket.sendto(str(response).encode(),(table[package["name"]][1],table[package["name"]][2]))
                        serverSocket.close()
                       
                        
                        
                        #print("LOLOL")
                        listySocket = socket(AF_INET, SOCK_DGRAM)
                        listySocket.bind(('', serverPort))
                        listySocket.setblocking(0)

                        ready = select.select([listySocket], [], [], 0.1)
                        # input("funny")
                        if ready[0]:
                            # input("gag")
                            listySocket.close()
                            for x in offline_messages[package["name"]]:
                                ## send received message to those active, add store to nonactive
                                name, timestamp, message, fromGC=x
                                # input(str(x)+"?")
                                sending_msg=" [Offline Message sent at "+timestamp+" received by "+package["name"]+".]"
                                if fromGC==False:

                                    if name!=None and table[name][3]==True:

                                        #listySocket.close()
                                        confirms=dict()
                                        confirms["type"]="msg"
                                        confirms["msg"]=message
                                        # input("with1")
                                        confirms["name_from"]=None
                                        # input("with2")
                                        confirms["msg"]=sending_msg
                                        # input("with")
                                        serverSocket = socket(AF_INET, SOCK_DGRAM)
                                        serverSocket.bind(('', serverPort))
                                        serverSocket.sendto(str(confirms).encode(),(table[name][1],table[name][2]))
                                        serverSocket.close()
                                        sleep(.1)
                                        # input("a")

# 
                                    elif name!=None and table[name][3]==False:
                                        new_offline_message=[None,timestamp,sending_msg,False]
                                        # if table[nam][3]==False:
                                        if offline_messages[name]:
                                            temp=offline_messages[name]
                                            
                                            temp.append(new_offline_message)
                                            
                                            offline_messages[name]=temp
                                        else:
                                            offline_messages[name]=[new_offline_message]




                                offline_messages[package["name"]]=[]
                                #print("successfull ofline transfer")
                            #input("stick")

                        #else:

                           # print(">>> reg "+package["name"]+ " fail")
                        # input("extra funnt")
                        # listySocket.close()

                        serverSocket.close()
                        #serverSocket.sendto(str(response).encode(),(table[package["name"]][1],table[package["name"]][2]))

                        
                        
                    elif package["type"]=="GC":
                        #input(str(offline_messages))

                        fromName=package["name"]
                        serverSocket.close()

                        sending=dict()
                        sending["type"]="ack"
                        sending["from"]="server"

                        toackClientIP=table[fromName][1]
                        toackClientPort=table[fromName][2]

                        serverSocket = socket(AF_INET, SOCK_DGRAM)
                        #serverSocket.bind(('', serverPort))
                        serverSocket.sendto(str(sending).encode(),(toackClientIP,toackClientPort))
                        serverSocket.close()



                        #serverSocket.close()
                        waiting_response=set()
                        seen_response=set()
                        for key in table.keys():

                            if table[key][3]==True and (key!=fromName):
                                # input("H-1?")
                                waiting_response.add(key)
                                serverSocket = socket(AF_INET, SOCK_DGRAM)
                                #serverSocket.bind(('', serverPort))
                                serverSocket.sendto(str(package).encode(),(table[key][1],table[key][2]))
                                serverSocket.close()
                                
                                
                                listySocket = socket(AF_INET, SOCK_DGRAM)
                                listySocket.bind(('', serverPort))
                                listySocket.setblocking(0)

                                ready = select.select([listySocket], [], [], 0.1)
                                # input("H0?")
                                if ready[0]:
                                    # input("H1?")
                                    rec_pac, fromAddress = listySocket.recvfrom(2048)
                                    rec_pac=eval(rec_pac.decode())
                                    # input("H1.5?")
                                    if rec_pac["type"]=="ack":
                                        seen_response.add(rec_pac["from"])
                                    # input("H3?")
                                # else:
                                    # input("H2?")
                                    # print("??q?Q??????")
                                    # print("seen: "+str(seen_response))
                                    # print("waiting: "+str(waiting_response))
                                listySocket.close()
                                # # input("H5?")
                                # print("seen: "+str(seen_response))
                                # print("waiting: "+str(waiting_response))

                            elif (table[key][3]==False):
                                ##offline message
                                timestamp=getTime()
                                #input("WERE HERE")
                                new_offline_message=[fromName,timestamp,package["message"],True]
                                if offline_messages[key]:
                                    temp=offline_messages[key]
                                    #input("OG offline_message: "+str(temp))
                                    temp.append(new_offline_message)
                                    #input("New offline_message: "+str(temp))
                                    offline_messages[key]=temp
                                else:
                                    offline_messages[key]=[new_offline_message]
                                #print(offline_messages)



                        for x in seen_response:
                            waiting_response.remove(x)
                        #input("H10?")
                        if len(waiting_response)>0:
                            for x in waiting_response:
                                entry=list(table[x])
                                new_entry=entry
                                new_entry[3]=False
                                table[x]=tuple(new_entry)
                            # input("past")
                            print(">>> [Client table updated.]")
                            print(table)
                            broadcast=dict()
                            broadcast["type"]="table_update"
                            broadcast["table"]=table
                            #input("inex2")
                            serverSocket = socket(AF_INET, SOCK_DGRAM)
                            for key in table.keys():
                                if table[key][3]==True:

                                    serverSocket.sendto(str(broadcast).encode(),(table[key][1],table[key][2]))
                                
                            serverSocket.close()
                                

                        serverSocket.close() 
                    

                    elif package["type"]=="to_offline":
                        #input(str(offline_messages))
                        fromName=package["name_from"]
                        toName=package["name_to"]
                        timestamp=package["timestamp"]
                        message=package["message"]


                        ###ALREADY MARKED OFFLINE
                        if table[toName][3]==False:
                            sending=dict()
                            sending["type"]="ack"
                            sending["from"]="server"
                            serverSocket.close()
                            toackClientIP=table[fromName][1]
                            toackClientPort=table[fromName][2]

                            serverSocket = socket(AF_INET, SOCK_DGRAM)
                            serverSocket.bind(('', serverPort))
                            serverSocket.sendto(str(sending).encode(),(toackClientIP,toackClientPort))
                            serverSocket.close()

                            new_offline_message=[fromName,timestamp,package["message"],False]
                            if table[toName][3]==False:
                                if offline_messages[toName]:
                                    temp=offline_messages[toName]
                                    
                                    temp.append(new_offline_message)
                                    
                                    offline_messages[toName]=temp
                                else:
                                    offline_messages[toName]=[new_offline_message]
                        
                        ###VERIFY
                        else:
                            
                            print("status check")
                            serverSocket.close()
                            sending=dict()
                            sending["type"]="status_check"
                            #sending["from"]="server"

                            toackClientIP=table[toName][1]
                            toackClientPort=table[toName][2]

                            serverSocket = socket(AF_INET, SOCK_DGRAM)
                            serverSocket.bind(('', serverPort))
                            serverSocket.sendto(str(sending).encode(),(toackClientIP,toackClientPort))
                            serverSocket.close()


                            ##ACK
                            serverSocket = socket(AF_INET, SOCK_DGRAM)
                            serverSocket.bind(('', serverPort))
                            serverSocket.setblocking(0)

                            ready = select.select([serverSocket], [], [], 0.1)
                            if ready[0]:
                                
                                #print("CLIENT IS ONLINE OOP")
                                package, clientAddress = serverSocket.recvfrom(2048)
                                #print(clientAddress)
                                #print(message)
                                print(package.decode())
                                serverSocket.close()

                                #Send err

                                error=dict()
                                error["type"]="error"
                                error["message"]=" [Client "+toName+" exists!!]"
                                #error["table"]=
                                

                                serverSocket = socket(AF_INET, SOCK_DGRAM)
                                serverSocket.bind(('', serverPort))
                                serverSocket.sendto(str(error).encode(),(table[fromName][1],table[fromName][2]))
                                serverSocket.close()


                                broadcast=dict()
                                broadcast["type"]="table_update"
                                broadcast["table"]=table
                                

                                serverSocket = socket(AF_INET, SOCK_DGRAM)
                                serverSocket.bind(('', serverPort))
                                serverSocket.sendto(str(broadcast).encode(),(table[fromName][1],table[fromName][2]))
                                serverSocket.close()


                                ##SEND ERR



                            else:
                                print("need to update")
                                entry=list(table[toName])
                                new_entry=entry
                                new_entry[3]=False

                                table[toName]=tuple(new_entry)

                                broadcast=dict()
                                broadcast["type"]="table_update"
                                broadcast["table"]=table
                                #input("inex2")
                                for key in table.keys():
                                    if table[key][3]==True:

                                        serverSocket.sendto(str(broadcast).encode(),(table[key][1],table[key][2]))
                                    
                                serverSocket.close()

                                new_offline_message=[fromName,timestamp,package["message"],False]
                                if table[toName][3]==False:
                                    if offline_messages[toName]:
                                        temp=offline_messages[toName]
                                        
                                        temp.append(new_offline_message)
                                        
                                        offline_messages[toName]=temp
                                    else:
                                        offline_messages[toName]=[new_offline_message]



                        serverSocket.close() 
                        


                        
        else:
            print("Invalid Arg Count")
            #input()

    ##Client Mode
    elif mode=="-c":
        if len(sys.argv)==6:
            #print("MO")
            serverName = sys.argv[3]
            serverPort = int(sys.argv[4])
            clientregSocket = socket(AF_INET, SOCK_DGRAM)
            
            name=sys.argv[2]
            clientPort= int(sys.argv[5])
            message = (name,clientPort)

            listenSocket = socket(AF_INET, SOCK_DGRAM)
            listenSocket.bind(('', clientPort))


            #print("Sending to:"+str((serverName, serverPort)))
            #input()
            print(">>> ",end="")
            package=dict()
            package["type"]="freg"
            package["message"]=message
            clientregSocket.sendto(str(package).encode(),(serverName, serverPort))
            clientregSocket.close()
            modifiedMessage, serverAddress = listenSocket.recvfrom(2048)


            
            response=eval(modifiedMessage.decode())

            if response["type"]=="conf_reg":
                table=dict()
                table=response["table"]
                print("[Welcome, You are registered.]")
                info=dict()
                info["table"]=table
                info["active"]=True
                info["serverIP"]=serverName
                info["serverPort"]=serverPort
                info["clientPort"]=clientPort
                info["clientName"]=name
                info["QUIT"]=False
                info["resend"]=False

                #print("Table:"+str(info["table"]))
                
                
                listenSocket.close()
                #input("A2")
                restart_event = threading.Event()
                #request_list=[False]
                receive_thread = threading.Thread(target=receive_data, args=(clientPort, restart_event))
                input_thread = threading.Thread(target=input_command, args=(name, restart_event))

                receive_thread.start()
                input_thread.start()

                ##Comm
                
                while info["QUIT"]==False:
                    restart_event.wait()
                    restart_event.clear()
            else:
                print("[Invalid Name]")
                input()
                
        else:
            print("Invalid Arg Count")
            input()
    else:
        print("Invalid Mode")

