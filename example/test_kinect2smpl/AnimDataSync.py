import struct
import random
import threading
import asyncio
import time
# import PythonWebWocketServer #调用以前的接口尝试转换数据并打印，用来跟服务器转换数据做比对

#网络包协议如下
#[
#uint32 包体长度，包括自身的4个字节

#uint32 协议类型
    # 0 注册channel通道协议。每个网络同步通道需要注册一个通道名称，以便服务器能够对应到相应的骨骼数据
    # 1 发送动作数据协议
    # 2 服务器注册通道反馈
    # 3 服务器动作反馈包

#data 协议数据。数据按不同协议，格式如下
    # 0 注册channel通道协议
        # string 通道名称。 

    # 1 发送动作数据协议
        # uint32 frame_id 帧ID
        # float[] animation_data 动作数据

    # 2 服务器注册通道反馈，没有协议数据

    # 3 服务器动作反馈。正常情况下不需要处理
        # uint32 frame_id 帧ID
#]

#--------------------------
#协议号定义
PROTO_CS_REGISTER_CHANNEL = 0
PROTO_CS_ANIM_DATA = 1
PROTO_SC_REGISTER_CHANNEL = 2
PROTO_SC_ANIM_DATA = 3
#---------------------------

class AnimDataSync:
    def __init__(self, ip, port, channel):
        self.ip = ip  #目标服务器地址
        self.port = port #目标服务器端口
        self.channel = channel #通道名称，用于服务器定位相关的配置数据。

        #发送缓存
        self.send_buffer_lock = threading.Lock()
        self.send_buffer = []

        #服务状态
        self.server_state_lock = threading.Lock()
        self.server_state = 0  #0未开启  1运行中  2关闭中

        self.recv_buffer_lock = threading.Lock()
        self.recv_buffer = []

        self.msgs = []

    #开启服务
    def start(self):
        self.server_thread = threading.Thread(target=self.run_server_thread, daemon=True)
        self.server_thread.start()
        
    #关闭服务
    def stop(self):
        if self.get_server_state() != 1:            
            return
        self.set_server_state(2)
        self.server_thread.join()

    #获取服务状态
    def get_server_state(self):
        with self.server_state_lock:
            return self.server_state

    #发送动作数据
    def send_anim_data(self, frameID, data):
        binary_data = struct.pack('!2I%df' % len(data), PROTO_CS_ANIM_DATA, frameID, *data)
        self.send_packet(binary_data)

    #取一条消息
    #取出的消息结构为 map
    #mapdata[id] = msg_id
    #其余数据根据协议不同自动赋值
    def pop_msg(self):

        with self.recv_buffer_lock:
            all_recv_data = self.recv_buffer[:]
            self.recv_buffer.clear()
        
        for data in all_recv_data:
            msg = {}
            msg_id = struct.unpack("!I", data[0:4])[0]
            msg["id"] = msg_id
            if msg_id == PROTO_SC_REGISTER_CHANNEL:
                print(f"注册通道{self.channel}成功")
            elif msg_id == PROTO_SC_ANIM_DATA:
                frame_id = struct.unpack("!I", data[4:])[0]
                msg["frame_id"] = frame_id
                print(f"帧{frame_id}服务器处理完成")                
            self.msgs.append(msg)

        if len(self.msgs) == 0:
            return None
        else:
            return self.msgs.pop(0)

    def register_channel(self, channel_name):
        s = channel_name.encode('utf-8')
        binary_data = struct.pack('!I%ds'% len(s), PROTO_CS_REGISTER_CHANNEL, s)
        self.send_packet(binary_data)


    # #发送数据
    # def send(self, data):
    #     # 将 float 数组转换为二进制字符串
    #     binary_data = struct.pack('!%df' % len(data), *data)

    #     # 计算数据包长度并将其转换为 4 字节二进制字符串
    #     packet_length = struct.pack('!I', len(binary_data) + 4)

    #     # 将数据包加入缓冲区
    #     with self.send_buffer_lock:
    #         self.send_buffer.append(packet_length + binary_data)    
        
    def send_packet(self, packet_data):
        packet_length = len(packet_data) + 4
        packet_length = struct.pack('!I', len(packet_data) + 4)
        with self.send_buffer_lock:
            self.send_buffer.append(packet_length + packet_data) 
        
    def push_recv_data(self, data):
        with self.recv_buffer_lock:
            self.recv_buffer.append(data)

    def run_server_thread(self):
        asyncio.run(self.run_server())

    def set_server_state(self, state):
        with self.server_state_lock:
            self.server_state = state
    
    async def run_server(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        except Exception as e:
            print(f"连接远程服务器失败 {e}")
            return

        print(f"连接到远程服务器成功 {self.ip}:{self.port}")
        self.set_server_state(1)

        #开启发送协程
        self.send_task = asyncio.create_task(self.send_loop())

        #注册channel
        self.register_channel(self.channel)

        #读取数据包添加到recv_buffer
        while True:
            
            if self.get_server_state() == 2:
                break

            try:
                packet_length = await self.reader.readexactly(4)
                packet_length = struct.unpack('!I', packet_length)[0]
                data_length = packet_length - 4
                data = await self.reader.readexactly(data_length)
                # data = struct.unpack('!%df' % (data_length // 4), data)
                self.push_recv_data(data)
                # print('Received:', data)
            except asyncio.IncompleteReadError as e:
                self.set_server_state(2)
                print("网络关闭", e)
                break
            except Exception as e:
                self.set_server_state(2)
                print("收数据异常", e)
                break
            
            await asyncio.sleep(0.02)

        try:
            self.reader.close()
            await self.reader.wait_closed()
        except:
            pass
        self.reader = None

        await self.send_task
        self.send_task = None

        self.set_server_state(0)

        print("server stopped")
        
    async def send_loop(self):
        while True:
            
            if self.get_server_state() == 2:
                break
            
            with self.send_buffer_lock:
                data_to_send = self.send_buffer[:]
                self.send_buffer.clear()

            for data in data_to_send:
                try:
                    self.writer.write(data)
                    await self.writer.drain()
                except Exception as e:
                    self.set_server_state(2)
                    print(f"发送数据失败: {e}")
                    return
                
            await asyncio.sleep(0.02)
        
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass
        self.writer = None

def main(ip, port, channel):
    #开始服务
    client = AnimDataSync(ip, port, channel)
    client.start()

    time.sleep(1)

    #发随机数据
    data = [random.uniform(0, 1) for _ in range(75)]
    print("send:", data)
    client.send_anim_data(0, data)

    #发随机数据
    data = [random.uniform(0, 1) for _ in range(75)]
    print("send:", data)
    client.send_anim_data(1, data)

    time.sleep(1)

    #收到的数据（若有）
    msg = client.pop_msg()
    if not msg is None:
        print("recv msg:", msg)

    #停止服务
    client.stop()

    time.sleep(1)
    
    #交互测试
    asyncio.run(interaction_test(ip, port, channel))

    print("bye!")


async def interaction_test(ip, port, channel):
    client = AnimDataSync(ip, port, channel)
    client.start()

    await asyncio.sleep(1)

    print("exit:退出; send:发送随机数据; send30fps <time>:以30fps的频率发送随机数据,持续指定秒数; pop:输出收到的数据; start:如果服务停，则重新连接")

    frame_id = 0
    while True:
        print(">", end="")
        # 接收用户输入的指令
        user_input = input()

        # 如果输入exit，则调用AnimDataSync.shutdown函数结束线程并退出程序
        if user_input == 'exit':            
            client.stop()
            break

        elif user_input == "start":
            if client.get_server_state() == 0:
                client.start()
            else:
                print("服务未停止")

        #检查服务状态
        elif client.get_server_state() != 1:
            print("服务未运行")        

        #发送随机数据
        elif user_input == "send":
            data = [random.uniform(0, 1) for _ in range(75)]
            client.send_anim_data(frame_id, data)
            frame_id = frame_id + 1
            print('Sending:', data)

            # #调用原来的转换函数，跟服务器输出的数据比对
            # data_factory_ue_result = PythonWebWocketServer.data_factory_ue(data)
            # print('data_factory_ue result:', data_factory_ue_result)
            # #更可视化的输出
            # for i in range(len(data_factory_ue_result)//4):
            #     print(f"[{i}]:[{data_factory_ue_result[4 * i]},{data_factory_ue_result[4 * i + 1]},{data_factory_ue_result[4 * i + 2]},{data_factory_ue_result[4 * i + 3]}]")

        #发送随机数据
        elif user_input.startswith("send30fps"):
            try:
                t = int(user_input.split(" ")[1])
                cnt = t * 1000 // 30
                for _ in range(cnt):
                    data = [random.uniform(0, 1) for _ in range(75)]
                    client.send_anim_data(frame_id, data)
                    frame_id = frame_id + 1
                    print('Sending:', data)
                    await asyncio.sleep(0.033)
                print("done")
            except:
                print("invalid cmd")

        #输出一条收到的消息
        elif user_input == "pop":
            print(client.pop_msg())

        elif len(user_input) > 0:
            print('Invalid input')

if __name__ == '__main__':
    main('127.0.0.1', 8123, "monkey")