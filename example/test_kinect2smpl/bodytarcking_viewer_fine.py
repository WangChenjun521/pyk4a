import numpy as np
import os
# from dual_quaternions import Quaternion
from AnimDataSync import AnimDataSync
import asyncio
import time
from scipy.spatial.transform import Rotation


# result_array[frame_id][joints_id][pos + roatation + conf]
def get_data(data_path):
    num_files = len(os.listdir(data_path))
    position = np.zeros((num_files, 32, 3))
    matrix = np.zeros((num_files, 32, 3, 3))
    axis_angle = np.zeros((num_files, 32, 3))
    rotation = np.zeros((num_files, 32, 4))
    conf = np.zeros((num_files, 32, 1))
    frame_id = 0
    for file_name in os.listdir(data_path):
        file_path = os.path.join(data_path, file_name)
        with open(file_path, 'r') as f:
            lines = f.readlines()

            for i, line in enumerate(lines):
                str_values = line.split()
                float_values = [float(s) for s in str_values]
                position[frame_id][i][0]=float_values[0]
                position[frame_id][i][1]=float_values[1]
                position[frame_id][i][2]=float_values[2]
                rotation[frame_id][i]=float_values[3:7]
                # as_matrix

                rot = Rotation.from_quat(np.asarray([rotation[frame_id][i][1], rotation[frame_id][i][2], rotation[frame_id][i][3],rotation[frame_id][i][0]])) 
                matrix[frame_id][i] = rot.as_matrix()
                axis_angle[frame_id][i]=rot.as_rotvec()
                # matrix[frame_id][i]=Quaternion.as_matrix(Quaternion( rotation[frame_id][i][0], rotation[frame_id][i][1], rotation[frame_id][i][2], rotation[frame_id][i][3]))
                # axis_angle[frame_id][i]=Quaternion.as_axis_anlge(Quaternion( rotation[frame_id][i][0], rotation[frame_id][i][1], rotation[frame_id][i][2], rotation[frame_id][i][3]))
                
                
                conf[frame_id][i]=float_values[7]
        frame_id +=1
    return position,rotation,matrix,axis_angle,conf


def kinect2smpl(data):
    res = np.zeros((24,3))
    with open("example/test_kinect2smpl/kinect2smpl.txt", 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            str_values = line.split()
            m = str_values[0]
            n = str_values[1]
            # if(int(m) ==6):
            #     print(n)
            # if(int(n) ==13):
            #     print("m=",m)
            if (int(n)<9999):
                res[int(n)]= data[int(m)]

    return res

def matrix2axis(m,ax,parent_list,r):
    relative_axs = np.zeros_like(ax)
    ry = Rotation.from_euler('y', 90, degrees=True)
    rot_y_90 = ry.as_matrix()
    ry3 = Rotation.from_euler('y', 270, degrees=True)
    rot_y_270 = ry3.as_matrix()
    nry = Rotation.from_euler('y', -90, degrees=True)
    rot_y_n_90 = nry.as_matrix()
    ry1 = Rotation.from_euler('y', 180, degrees=True)
    rot_y_180 = ry1.as_matrix()
    rz = Rotation.from_euler('z', 90, degrees=True)
    rot_z_90 = rz.as_matrix()
    rz_ = Rotation.from_euler('z', -270, degrees=True)
    rot_z_n_270 = rz_.as_matrix()
    rz1 = Rotation.from_euler('z', 180, degrees=True)
    rot_z_180 = rz1.as_matrix()
    rz1n = Rotation.from_euler('z', -90, degrees=True)
    rot_z_n_90 = rz1n.as_matrix()
    r1 = Rotation.from_euler('x', 90, degrees=True)
    rot_x_90 = r1.as_matrix()
    r1n = Rotation.from_euler('x', -90, degrees=True)
    rot_x_n_90 = r1n.as_matrix()
    r_ = Rotation.from_euler('x', 180, degrees=True)
    rot_x_180 = r_.as_matrix()
    r2 = Rotation.from_euler('x', -180, degrees=True)
    rot_x_n_180 = r2.as_matrix()
    
    for i in range(m.shape[0]):
        root_rot = np.asmatrix(m[i,0,:,:])  
        root_rot_i = Rotation.from_matrix(root_rot) 
        transform_ax = np.zeros(3)
        root_ax = root_rot_i.as_rotvec()
        root_rot_ = change_axis(root_ax,-1,-1,1,0,2,1) 
        root_rot_ = Rotation.from_rotvec(root_rot_)
        root_rot_m = root_rot_.as_matrix()    
        root_rot_m = np.dot(rot_x_90, root_rot_m)
        root_rot_m = np.dot(rot_y_90, root_rot_m)
        root_rot = Rotation.from_matrix(root_rot_m) 
        root_ax = root_rot.as_rotvec()
       
        relative_axs[i,0,:] = np.asarray(root_ax)
        for j in range(1, m.shape[1]):
            if (j==1) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()
                relative_rot_ = change_axis(relative_ax,-1,-1,1,0,2,1) 
               
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)     
            #already left arm
            elif (j==4 ) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax, -1,1,1,2,0,1) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot__m = np.dot(rot_z_90, relative_rot__m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax) 

            elif (j>=5 and j<=7) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax, -1,1,1,2,0,1) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                # root_rot_m = np.dot(rot_x_n_90, root_rot_m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax) 

            # right arm
            elif (j==11) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax, -1,-1,-1,2,0,1) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot__m = np.dot(rot_z_90, relative_rot__m)
                relative_rot__m = np.dot(rot_y_180, relative_rot__m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)   

            elif (j>=12 and j <=13) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax, -1,-1,-1,2,0,1)  
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax) 
            
            # left leg
            elif (j>=18 and j<=21) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                if (i==0 and j==19):
                    # np.savetxt("C:/data/debug/c/gloabal_1.txt",gloabal_rot)
                    # np.savetxt("C:/data/debug/c/parents_1.txt",parent_rot)
                    # np.savetxt("C:/data/debug/c/parents_inverse_1.txt",np.linalg.inv(parent_rot))
                    # np.savetxt("C:/data/debug/c/relative_rot_1.txt",relative_rot)
                    pass
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax,-1,-1,1,0,2,1) 
                if (i==0 and j==19):
                    # np.savetxt("C:/data/debug/c/relative_axis_angles.txt",relative_ax)
                    # np.savetxt("C:/data/debug/c/change_axis_angles.txt",relative_rot_)
                    pass
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                # root_rot_m = np.dot(rot_x_n_90, root_rot_m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax) 
        
            # right leg
            elif (j==22) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax,-1,1,-1,0,2,1)
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot__m = np.dot(rot_x_180, relative_rot__m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)  
            elif (j>=23 and j<=25) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax,-1,1,-1,0,2,1)
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax) 

            elif(j==26):
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                root_ax = root_rot_i.as_rotvec()
                root_rot_ = change_axis(root_ax,-1,-1,1,0,2,1) 
                root_rot_ = Rotation.from_rotvec(root_rot_)
                root_rot_m = root_rot_.as_matrix()
                root_rot = Rotation.from_matrix(root_rot_m) 
                root_ax = root_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(transform_ax)    
                
            else:
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                print(i)
                print(parent_list[j, 1])
                print(parent_rot)
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot = Rotation.from_matrix(relative_rot)
                relative_ax = relative_rot.as_rotvec()
                transform_ax[0] = -relative_ax[2]
                transform_ax[1] = relative_ax[1]
                transform_ax[2] = relative_ax[0]
                relative_axs[i,j,:]  = np.asarray(transform_ax)
    return relative_axs

def debugmatrix2axis(m, ax, info, parent_list, p, client):
    relative_axs = np.zeros_like(ax)
    ry = Rotation.from_euler('y', 90, degrees=True)
    rot_y_90 = ry.as_matrix()
    ry3 = Rotation.from_euler('y', 270, degrees=True)
    rot_y_270 = ry3.as_matrix()
    nry = Rotation.from_euler('y', -90, degrees=True)
    rot_y_n_90 = nry.as_matrix()
    ry1 = Rotation.from_euler('y', 180, degrees=True)
    rot_y_180 = ry1.as_matrix()
    rz = Rotation.from_euler('z', 90, degrees=True)
    rot_z_90 = rz.as_matrix()
    rz_ = Rotation.from_euler('z', -270, degrees=True)
    rot_z_n_270 = rz_.as_matrix()
    rz1 = Rotation.from_euler('z', 180, degrees=True)
    rot_z_180 = rz1.as_matrix()
    rz1n = Rotation.from_euler('z', -90, degrees=True)
    rot_z_n_90 = rz1n.as_matrix()
    r1 = Rotation.from_euler('x', 90, degrees=True)
    rot_x_90 = r1.as_matrix()
    r1n = Rotation.from_euler('x', -90, degrees=True)
    rot_x_n_90 = r1n.as_matrix()
    r_ = Rotation.from_euler('x', 180, degrees=True)
    rot_x_180 = r_.as_matrix()
    r2 = Rotation.from_euler('x', -180, degrees=True)
    rot_x_n_180 = r2.as_matrix()
    
    for i in range(1,110):
        root_rot = np.asmatrix(m[i,0,:,:])  
        root_rot_i = Rotation.from_matrix(root_rot) 
        transform_ax = np.zeros(3)
        root_ax = root_rot_i.as_rotvec()
        root_rot_ = change_axis(root_ax,-1,-1,1,0,2,1) 
        root_rot_ = Rotation.from_rotvec(root_rot_)
        root_rot_m = root_rot_.as_matrix()
        root_rot_m = np.dot(rot_x_90, root_rot_m)
        # root_rot_m = np.dot(rot_z_n_90, root_rot_m)
        root_rot_m = np.dot(rot_y_90, root_rot_m)
        root_rot = Rotation.from_matrix(root_rot_m) 
        root_ax = root_rot.as_rotvec()
        relative_axs[i,0,:] = np.asarray(root_ax)
        for j in range(1, m.shape[1]):
            if (j>=1 and j<=3) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                root_ax = root_rot_i.as_rotvec()
                root_rot_ = change_axis(root_ax,-1,-1,1,0,2,1) 
                root_rot_ = Rotation.from_rotvec(root_rot_)
                root_rot_m = root_rot_.as_matrix()
                root_rot_m = np.dot(rot_x_90, root_rot_m)
                root_rot_m = np.dot(rot_y_90, root_rot_m)
                root_rot = Rotation.from_matrix(root_rot_m) 
                root_ax = root_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(transform_ax)        
            #already left arm
            elif (j==4 ) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                # relative_rot_ = change_axis_debug(relative_ax, info)
                relative_rot_ = change_axis(relative_ax, -1,1,1,2,0,1) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot__m = np.dot(rot_z_90, relative_rot__m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)   

            elif (j>=5 and j<=6) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis_debug(relative_ax, info) 
                # relative_rot_ = change_axis(relative_ax, -1,1,1,2,0,1) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                # root_rot_m = np.dot(rot_x_n_90, root_rot_m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)   

            elif (j==7) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                # relative_rot_ = change_axis_debug(relative_ax, info) 
                relative_rot_ = change_axis(relative_ax, -1,-1,1,2,1,0) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                root_rot_m = np.dot(rot_x_n_90, root_rot_m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)   
            elif (j==14) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                # relative_rot_ = change_axis_debug(relative_ax, info) 
                relative_rot_ = change_axis(relative_ax, -1,1,-1,2,1,0) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                # root_rot_m = np.dot(rot_x_n_90, root_rot_m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)  
            # right arm
            elif (j==11) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                # relative_rot_ = change_axis_debug(relative_ax, info) 
                relative_rot_ = change_axis(relative_ax, -1,-1,-1,2,0,1) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot__m = np.dot(rot_z_90, relative_rot__m)
                relative_rot__m = np.dot(rot_y_180, relative_rot__m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)   

            elif (j>=12 and j <=13) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                # relative_rot_ = change_axis_debug(relative_ax, info)
                relative_rot_ = change_axis(relative_ax, -1,-1,-1,2,0,1)  
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                # root_rot_m = np.dot(rot_x_n_90, root_rot_m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)   
            
            # left leg
            elif (j==18) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax,-1,-1,1,0,2,1) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax) 
            elif (j>=19 and j<=21) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                relative_rot_ = change_axis(relative_ax,-1,-1,1,0,2,1) 
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                # root_rot_m = np.dot(rot_x_n_90, root_rot_m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax) 
            # right leg
            elif (j==22) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                # relative_rot_ = change_axis_debug(relative_ax, info) 
                relative_rot_ = change_axis(relative_ax,-1,1,-1,0,2,1)
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot__m = np.dot(rot_x_180, relative_rot__m)
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)  
            elif (j>=23 and j<=25) :
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot_i = Rotation.from_matrix(relative_rot)
                transform_ax = np.zeros(3)
                relative_ax = relative_rot_i.as_rotvec()  
                # relative_rot_ = change_axis_debug(relative_ax, info) 
                relative_rot_ = change_axis(relative_ax,-1,1,-1,0,2,1)
                relative_rot_ = Rotation.from_rotvec(relative_rot_)
                relative_rot__m = relative_rot_.as_matrix()
                relative_rot = Rotation.from_matrix(relative_rot__m) 
                relative_ax = relative_rot.as_rotvec()
                relative_axs[i,j,:]  = np.asarray(relative_ax)  
            
            
            else:
                gloabal_rot = m[i,j,:,:]
                parent_rot =m[i, parent_list[j, 1], :, :]
                relative_rot = np.dot(gloabal_rot,np.linalg.inv(parent_rot))
                relative_rot = Rotation.from_matrix(relative_rot)
                relative_ax = relative_rot.as_rotvec()
                transform_ax[0] = -relative_ax[2]
                transform_ax[1] = relative_ax[1]
                transform_ax[2] = relative_ax[0]
                relative_axs[i,j,:]  = np.asarray(transform_ax)
        r_p = kinect2smpl(p[i])
        r_p = r_p/1000
        r_ax = kinect2smpl(relative_axs[i])
        data0 = r_p[0].reshape(-1).tolist()
        test = np.zeros_like(r_ax)
        data0[0] = data0[0]
        data0[1] = data0[1]
        data0[2] = data0[2]
        test[0] = r_ax[0]
        test[20] = r_ax[20]
        test[21] = r_ax[21]
        data1 = test.reshape(-1).tolist()
        data = data0 +data1
        client.send_anim_data(i, data)
        time.sleep(0.05)  
    return 1

def debug_axis():
    path = 'example/test_kinect2smpl/debug_info2.txt'
    root = 'example/test_kinect2smpl/show_time/'
    data_path = root + '0/'
    client = AnimDataSync('10.177.61.252', 8123, "virtualman")
    client.start()
    time.sleep(1)
    p,r,m,ax,c = get_data(data_path)
    parent_list = np.loadtxt('example/test_kinect2smpl/parent.txt').astype(int)
    with open(path, 'r') as f:
        lines = f.readlines()
    index = 0
    for line in lines:
        print("line", line)
        print("-------------row_num--------------:", index)
        index +=1
        debugmatrix2axis(m, ax, line, parent_list, p, client)
    return 1


def change_axis(root_ax,x_s,y_s,z_s,x_a,y_a,z_a):
    transform_ax = np.zeros(3)
    transform_ax[0] = x_s * root_ax[x_a]
    transform_ax[1] = y_s * root_ax[y_a]
    transform_ax[2] = z_s * root_ax[z_a]
    return transform_ax

# axis 48 types
def change_axis_debug(root_ax,info):
    transform_ax = np.zeros(3)
    info = info.split(' ')
    transform_ax[0] = float(info[0]) * root_ax[int(info[3])]
    transform_ax[1] = float(info[1]) * root_ax[int(info[4])]
    transform_ax[2] = float(info[2]) * root_ax[int(info[5])]
    return transform_ax


def k4a_test():
    import cv2

    import pyk4a
    # from helpers import colorize
    from pyk4a import ColorResolution, Config, PyK4A


    k4a = PyK4A(
        Config(
            color_resolution=ColorResolution.RES_720P,
            depth_mode=pyk4a.DepthMode.NFOV_UNBINNED,
            camera_fps=pyk4a.FPS.FPS_30,
        )
    )
    k4a.start()
    client = AnimDataSync('10.177.61.252', 8123, "virtualman")
    client.start()
    time.sleep(1)
    index=0
    while True:
        
        capture = k4a.get_capture()
        body_skeleton = capture.body_skeleton

        if body_skeleton is None:
            time.sleep(2)
            continue
        else:
            index+=1
        
        print(body_skeleton)
        # skeleton = body_skeleton[0, :, :3]
        p = np.copy(body_skeleton[0, :, :3])
        r = np.copy(body_skeleton[0, :, 3:7])
        c=np.copy(body_skeleton[0, :, 7])
        rotation_temp=np.roll(r, -1, axis=1)

        print("r:",r[0])
        print("p:",p[0])
        rot = Rotation.from_quat(rotation_temp) 


        m = rot.as_matrix()
        ax=rot.as_rotvec()
        
        print("ax:",ax[0])
        # print("position:",position.shape)
        # print("rotation:",rotation.shape)
        # print("matrix:",matrix.shape)
        # print("axis_angle:",axis_angle.shape)
        parent_list = np.loadtxt('example/test_kinect2smpl/parent.txt').astype(int)
        relative_axs = np.zeros_like(ax.reshape(1,ax.shape[0],ax.shape[1]))
        relative_axs = matrix2axis(m.reshape(1,m.shape[0],m.shape[1],m.shape[2]),ax.reshape(1,ax.shape[0],ax.shape[1]),parent_list,r.reshape(1,r.shape[0],r.shape[1]))
        # body_pose = d['pose'][0, :, 2:5]
        r_p = kinect2smpl(p)
        r_p = r_p/1000
        r_ax = kinect2smpl(relative_axs[0])
        data0 = r_p[0].reshape(-1).tolist()
        data0[0] = data0[0]
        data0[1] = data0[1]
        data0[2] = data0[2]
        r_ax[20] = np.asarray([0,0,0])
        # r_ax[21] = np.asarray([0,0,0])
        data1 = r_ax.reshape(-1).tolist()
        data = data0 + data1
        # path = "C:/data/debug/motion/%06d.txt",i
        # np.savetxt("C:/data/debug/motion/%06d.txt"%i,data)
        # print(len(data))
        # time.sleep(1)
        # print(data)
        client.send_anim_data(index, data)
        # time.sleep(0.06)



if __name__ == "__main__":


    k4a_test()
    # debug_axis()
    # root = 'C:/Vimiku/KinectData/3d_viewer_data/'
    root = 'example/test_kinect2smpl/show_time/'
    data_path = root + '0/'
    p,r,m,ax,c = get_data(data_path)
    parent_list = np.loadtxt('example/test_kinect2smpl/parent.txt').astype(int)
    relative_axs = np.zeros_like(ax)

    relative_axs = matrix2axis(m,ax,parent_list,r)

    # axis_angle = Quaternion.as_axis_anlge(q)
    client = AnimDataSync('10.177.61.252', 8123, "virtualman")
    client.start()
    time.sleep(1)
    # print(len(os.listdir(data_path)))
    for i in range(len(os.listdir(data_path))):
        r_p = kinect2smpl(p[i])
        r_p = r_p/1000
        r_ax = kinect2smpl(relative_axs[i])
        data0 = r_p[0].reshape(-1).tolist()
        data0[0] = data0[0]
        data0[1] = data0[1]
        data0[2] = data0[2]
        r_ax[20] = np.asarray([0,0,0])
        # r_ax[21] = np.asarray([0,0,0])
        data1 = r_ax.reshape(-1).tolist()
        data = data0 + data1
        path = "C:/data/debug/motion/%06d.txt",i
        # np.savetxt("C:/data/debug/motion/%06d.txt"%i,data)
        # print(len(data))
        time.sleep(1)
        print(data)
        client.send_anim_data(i, data)
        time.sleep(0.06)
