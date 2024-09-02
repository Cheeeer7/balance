import pandas as pd
from fountions import setup_table
from PyQt5.QtWidgets import QMessageBox,QLabel
from PyQt5.QtCore import Qt
import numpy as np
import math
from PyQt5.QtGui import QFont

def balance_prepare(self,point_data,ori_data,rem_data,out_condition):
    tip='-1'
    index_list=[]
    self.is_circle=False
    recode=False
    sum_distance=0
    if out_condition=='fr':
        tip='往测点号'
    elif out_condition=='bk':
        tip='反测点号'
    for index, row in point_data.iterrows():
        temp=row[tip]
        index_list.append(temp)
    if index_list[-1]==ori_data['点号'].iloc[-1]:
        pass
    else:
        index_list.append(ori_data['点号'].iloc[-1])
        self.is_circle=True
    lengh_frame = pd.concat([ori_data,ori_data],axis=0)
    for i in range(1,len(index_list)):
        from_point=index_list[i-1]
        goal_point=index_list[i]
        point=from_point+"->"+goal_point
        high_change=0
        for length_index, length_row in lengh_frame.iterrows():
            if length_row['点号']==from_point:
                from_point_high=length_row['高程']
                recode=True
            if length_row['点号']==goal_point and recode==True:
                recode=False
                goal_point_high=length_row['高程']
                high_change=goal_point_high-from_point_high
                break
            if recode==True:
                sum_distance+=length_row['到下点距离']
        temp_data={
            '测段':[point],
            '高程变化':[high_change],
            '距离':[sum_distance],
        }
        line_data=pd.DataFrame(temp_data)
        rem_data=pd.concat([rem_data,line_data],ignore_index=True)
        high_change=sum_distance=0
    if out_condition=='fr':
        self.para_dis_fr=rem_data
        setup_table(self,rem_data,self.ui.tableWidget_7)
    elif out_condition=='bk':
        self.para_dis_bk=rem_data
        setup_table(self,rem_data,self.ui.tableWidget_8)
        
def balance_(self,edge_data,point_data,direction_logo):
    i=0
    temp=[]
    global A_matrix,Q_matrix,N_aa_matrix
    for index, row in point_data.iterrows():
        if row['控制高程']=='待求':
            i+=1
        else:
            temp.append(row['点名'])
    if self.is_circle==True:
        temp.append(temp[0])
    A_column_num=edge_data.shape[0]
    A_row_nun=A_column_num-i
    A_matrix=np.zeros((A_row_nun,A_column_num))
    W_matrix=np.zeros((A_row_nun,1))
    Q_matrix=np.zeros((A_column_num,A_column_num))
    temp_point_dataframe=pd.concat([point_data,point_data],axis=0)
    remember=False
    L_matrix=edge_data['高程变化'].values.reshape(-1,1)
    for j in range(1,len(temp)):
        from_point_sign=temp[j-1]
        goal_point_sign=temp[j]
        for point_index, point_row in temp_point_dataframe.iterrows():
            if point_row['点名']==from_point_sign:
                remember=True
            if point_row['点名']==goal_point_sign and remember==True:
                remember=False
                break
            if remember==True:
                if point_index>point_data.shape[0]:
                    insert_index=point_index-point_data.shape[0]
                else:
                    insert_index=point_index
                W_matrix[j-1,0]+=float(edge_data.iloc[insert_index,1])
                A_matrix[j-1,insert_index]=1
        for point_index, point_row in temp_point_dataframe.iterrows():
            if point_row['点名']==from_point_sign:
                from_point_high=float(point_row['控制高程'])
            if point_row['点名']==goal_point_sign:
                goal_point_high=float(point_row['控制高程'])
        W_matrix[j-1,0]+=from_point_high-goal_point_high
    for point_index_Q, point_row_Q in edge_data.iterrows():
        Q_matrix[point_index_Q,point_index_Q]=point_row_Q['距离']
    #print(W_matrix)        
    #print(A_matrix)
    #print(Q_matrix)
    D=np.dot(A_matrix,Q_matrix)
    N_aa_matrix=np.dot(D,A_matrix.T)
    K_matrix=(-1)*np.dot(np.linalg.inv(N_aa_matrix),W_matrix)
    V_matrix=np.linalg.multi_dot([Q_matrix,A_matrix.T,K_matrix])
    L_balance_matrix=V_matrix+L_matrix
    #print("111")
    #print(L_matrix)        
    #print(W_matrix)
    #print(K_matrix)
    #print(V_matrix)
    #print(L_balance_matrix)
    show_list=matrix_to_str_list(A_matrix,W_matrix)
    update_listWidget(show_list,self.ui.listWidget)
    update_label(A_matrix,self.ui.label_11,15)
    update_label(W_matrix,self.ui.label_12,15)
    update_label(Q_matrix,self.ui.label_15,10)
    update_label(K_matrix,self.ui.label_17,10)
    update_label(N_aa_matrix,self.ui.label_19,10)
    update_label(L_balance_matrix,self.ui.label_21,10)
    #Z_matrix_object=np.array([[L_matrix.T,W_matrix.T,K_matrix.T,V_matrix.T,L_balance_matrix.T]], dtype=object)
    #print(Z_matrix_object.T)
    #Q_matrix_object=np.array([[Q_matrix]], dtype=object)
    #print(f"2{Q_matrix_object}")
    #Q_zz_matrix = np.empty_like(Z_matrix_object, dtype=object)
    #for i in range(Z_matrix_object.shape[0]):
    #    for j in range(Z_matrix_object.shape[1]):
    #        Q_zz_matrix[i, j] = np.linalg.multi_dot([Z_matrix_object[i, j], Q_matrix_object[i, j], Z_matrix_object[i, j].T])
    #print(Q_zz_matrix)
    Q_ll=Q_matrix
    Q_lw=np.dot(Q_matrix,A_matrix.T)
    Q_lk=-1*Q_matrix@A_matrix.T@np.linalg.inv(N_aa_matrix)
    Q_lv=Q_lk@A_matrix@Q_matrix
    Q_ll_=Q_matrix+Q_lv
    Q_wl=A_matrix@Q_matrix
    Q_ww=N_aa_matrix
    Q_wk=-1*N_aa_matrix@np.linalg.inv(N_aa_matrix)
    Q_wv=-1*A_matrix@Q_matrix
    Q_wl_=0
    Q_kl=-1*np.linalg.inv(N_aa_matrix)@A_matrix@Q_matrix
    Q_kw=Q_wk
    Q_kk=np.linalg.inv(N_aa_matrix)
    Q_kv=np.linalg.inv(N_aa_matrix)@A_matrix@Q_matrix
    Q_kl_=0
    Q_vl=-1*Q_matrix@A_matrix.T@np.linalg.inv(N_aa_matrix)@A_matrix@Q_matrix
    Q_vw=-1*Q_matrix@A_matrix.T
    Q_vk=Q_matrix@A_matrix.T@np.linalg.inv(N_aa_matrix)
    Q_vv=-1*Q_vl
    Q_vl_=0
    Q_l_l=Q_ll_
    Q_l_w=0
    Q_l_k=0
    Q_l_v=0
    Q_l_l_=Q_matrix-Q_vv
    
    lables=['L','W','K','V','L^']
    matrix_list = [
    [Q_ll, Q_lw, Q_lk, Q_lv, Q_ll_],
    [Q_wl, Q_ww, Q_wk, Q_wv, Q_wl_],
    [Q_kl, Q_kw, Q_kk, Q_kv, Q_kl_],
    [Q_vl, Q_vw, Q_vk, Q_vv, Q_vl_],
    [Q_l_l, Q_l_w, Q_l_k, Q_l_v, Q_l_l_]
    ]
    self.show_precision = pd.DataFrame(matrix_list, index=lables, columns=lables)
    ttt=A_matrix.shape[0]
    ttf=A_matrix.shape[1]
    fi_or=-1*W_matrix.T@K_matrix
    self.fi=math.sqrt(float(fi_or.item())/ttt)
    fi_fr=-1
    self.bal_text=""
    for it in range(ttf):
        f_matrix=generate_f(ttf,it)
        self.ui.statusbar.showMessage("往测平差成功！")
        Q_fi_fi=f_matrix.T@Q_l_l_@f_matrix
        fi_fr=self.fi*math.sqrt(Q_fi_fi.item())
        self.bal_text=self.bal_text+f"第{int(it+1)}段的中误差为{fi_fr:.6f}\n"
    
    
    base_high_point=-1
    base_high=0
    for index_point, row_point in point_data.iterrows():
        if row_point['控制高程']!='待求':
            base_high_point=index_point
            base_high=float(row_point['控制高程'])
            break
    for point_index, point_row in temp_point_dataframe.iloc[base_high_point:point_data.shape[0]+base_high_point].iterrows():
        if point_index>point_data.shape[0]:
            point_index_in=point_index-point_data.shape[0]
        else:
            point_index_in=point_index
        if direction_logo=='fr':
            self.fr_balance_data.loc[point_index_in,'平差高程']=base_high
            self.fr_balance_data.loc[point_index_in,'点名']=point_row['点名']
            self.fr_balance_data.loc[point_index_in,'点号']=point_row['往测点号']
        elif direction_logo=='bk':
            self.bk_balance_data.loc[point_index_in,'平差高程']=base_high
            self.bk_balance_data.loc[point_index_in,'点名']=point_row['点名']
            self.bk_balance_data.loc[point_index_in,'点号']=point_row['反测点号']
        base_high+=L_balance_matrix[point_index_in].item()
    if direction_logo=='fr':
        self.fr_balance_data=self.fr_balance_data.sort_index()
        setup_table(self,self.fr_balance_data,self.ui.tableWidget_9)
        self.ui.tabWidget_3.setCurrentIndex(2)
    if direction_logo=='bk':
        self.bk_balance_data=self.bk_balance_data.sort_index()
        setup_table(self,self.bk_balance_data,self.ui.tableWidget_10)
        self.ui.tabWidget_3.setCurrentIndex(3)
        
def update_listWidget(data,widge):
    widge.clear()
    for item in data:
        widge.addItem(str(item))
def update_label(matrix, label,font_size):
    label.setText("")
    font = QFont()
    font.setPointSize(font_size)
    matrix_str = "\n".join([" ".join(map(str, row)) for row in matrix])
    label.setText(matrix_str)
    label.setAlignment(Qt.AlignCenter)  # 设置文本居中对齐
    label.setFont(font)

def mixed_balance_(self,fr_data_,bk_data_):
    fr_data=fr_data_.rename(columns={'点名':'点名','点号':'往测点号','平差高程':'往测平差高程'})
    bk_data=bk_data_.rename(columns={'点名':'点名','点号':'反测点号','平差高程':'反测平差高程'})
    self.mixed_balance_data=pd.DataFrame({
            '点名':[],
            '往测平差高程':[],
            '反测平差高程':[],
            '往返均衡高程':[]
        })
    for index_point, row_point in fr_data.iterrows():
        print(row_point)
        sum_high=float(row_point['往测平差高程'])+float(bk_data.loc[index_point,'反测平差高程'])
        sum_high/=2
        data={
            '点名':[row_point['点名']],
            '往测平差高程':[row_point['往测平差高程']],
            '反测平差高程':[bk_data.loc[index_point,'反测平差高程']],
            '往返均衡高程':[sum_high]
        }
        data_temp=pd.DataFrame(data)
        self.mixed_balance_data=pd.concat([self.mixed_balance_data,data_temp], ignore_index=True)
    setup_table(self,self.mixed_balance_data,self.ui.tableWidget_11)
    
def matrix_to_str_list(matrix1, matrix2):
    """处理矩阵a，重写条件方程"""
    result = []
    
    for row1, v in zip(matrix1, matrix2):
        expression = " + ".join([f"{x}*v{idx+1}" for idx, x in enumerate(row1)])
        expression += f" + {v[0]} = 0"
        result.append(expression)
    
    return result

def generate_f(n, pos):
    """
    生成一个长度为 n 的列向量，只有第 pos 个位置为 1，其余位置为 0。
    
    参数:
    n   : 向量的长度
    pos : 设置为 1 的位置索引（从 0 开始计数）
    
    返回:
    一个 n x 1 的列向量，其中第 pos 行的值为 1，其余为 0
    """
    # 初始化一个全为 0 的列向量
    vector = np.zeros((n, 1))
    
    # 设置指定位置为 1
    if 0 <= pos < n:
        vector[pos] = 1
    else:
        raise ValueError("pos 参数超出范围")
    
    return vector