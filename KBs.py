import numpy as np
import pickle
import itertools, collections, re
import copy
import random
import collections 
count = collections.Counter
identity = lambda x:x
# import collections
base2bin=lambda data,scale,num_of_bits: bin(int(data, scale))[2:].zfill(num_of_bits);
hex2bin=lambda hexdata,num_of_bits: base2bin(hexdata,16,num_of_bits);
bin2hex = lambda bitstr:hex(int(bitstr,2)).lstrip('0x').rstrip('L')

# from astropy.convolution import convolve
# convolve_int=lambda a,fir,method:np.around(convolve(a,fir,method)).astype(np.int);
import scipy.ndimage
convolve_int=lambda a,fir,method,**kwargs:scipy.ndimage.filters.convolve(a,fir,mode = method,**kwargs)

hensellist=['b0_','b1c','b1e','b2a','b2c','b3i','b2e','b3a','b2k','b3n','b3j','b4a','s0_','s1c','s1e','s2a','s2c','s3i','s2e','s3a','s2k','s3n','s3j','s4a','b2i','b3r','b3e','b4r','b4i','b5i','s2i','s3r','s3e','s4r','s4i','s5i','b2n','b3c','b3q','b4n','b4w','b5a','s2n','s3c','s3q','s4n','s4w','s5a','b3y','b3k','b4k','b4y','b4q','b5j','b4t','b4j','b5n','b4z','b5r','b5q','b6a','s3y','s3k','s4k','s4y','s4q','s5j','s4t','s4j','s5n','s4z','s5r','s5q','s6a','b4e','b5c','b5y','b6c','s4e','s5c','s5y','s6c','b5k','b6k','b6n','b7c','s5k','s6k','s6n','s7c','b4c','b5e','b6e','s4c','s5e','s6e','b6i','b7e','s6i','s7e','b8_','s8_',];
rca2ntca=[0, 1, 2, 3, 1, 4, 3, 5, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 13, 16, 15, 17, 14, 15, 18, 19, 20, 21, 22, 23, 2, 8, 6, 10, 3, 9, 7, 11, 24, 25, 26, 27, 25, 28, 27, 29, 14, 20, 18, 22, 15, 21, 19, 23, 30, 31, 32, 33, 31, 34, 33, 35, 1, 4, 8, 9, 36, 37, 38, 39, 3, 5, 10, 11, 38, 39, 40, 41, 13, 16, 20, 21, 42, 43, 44, 45, 15, 17, 22, 23, 44, 45, 46, 47, 8, 48, 49, 50, 38, 51, 52, 53, 25, 54, 55, 56, 57, 58, 59, 60, 20, 61, 62, 63, 44, 64, 65, 66, 31, 67, 68, 69, 70, 71, 72, 73, 2, 8, 24, 25, 8, 48, 25, 54, 6, 10, 26, 27, 49, 50, 55, 56, 14, 20, 30, 31, 20, 61, 31, 67, 18, 22, 32, 33, 62, 63, 68, 69, 6, 49, 26, 55, 10, 50, 27, 56, 26, 55, 74, 75, 55, 76, 75, 77, 18, 62, 32, 68, 22, 63, 33, 69, 32, 68, 78, 79, 68, 80, 79, 81, 3, 9, 25, 28, 38, 51, 57, 58, 7, 11, 27, 29, 52, 53, 59, 60, 15, 21, 31, 34, 44, 64, 70, 71, 19, 23, 33, 35, 65, 66, 72, 73, 10, 50, 55, 76, 40, 82, 59, 83, 27, 56, 75, 77, 59, 83, 84, 85, 22, 63, 68, 80, 46, 86, 72, 87, 33, 69, 79, 81, 72, 87, 88, 89, 1, 36, 8, 38, 4, 37, 9, 39, 8, 38, 49, 52, 48, 51, 50, 53, 13, 42, 20, 44, 16, 43, 21, 45, 20, 44, 62, 65, 61, 64, 63, 66, 3, 38, 10, 40, 5, 39, 11, 41, 25, 57, 55, 59, 54, 58, 56, 60, 15, 44, 22, 46, 17, 45, 23, 47, 31, 70, 68, 72, 67, 71, 69, 73, 4, 37, 48, 51, 37, 90, 51, 91, 9, 39, 50, 53, 51, 91, 82, 92, 16, 43, 61, 64, 43, 93, 64, 94, 21, 45, 63, 66, 64, 94, 86, 95, 9, 51, 50, 82, 39, 91, 53, 92, 28, 58, 76, 83, 58, 96, 83, 97, 21, 64, 63, 86, 45, 94, 66, 95, 34, 71, 80, 87, 71, 98, 87, 99, 3, 38, 25, 57, 9, 51, 28, 58, 10, 40, 55, 59, 50, 82, 76, 83, 15, 44, 31, 70, 21, 64, 34, 71, 22, 46, 68, 72, 63, 86, 80, 87, 7, 52, 27, 59, 11, 53, 29, 60, 27, 59, 75, 84, 56, 83, 77, 85, 19, 65, 33, 72, 23, 66, 35, 73, 33, 72, 79, 88, 69, 87, 81, 89, 5, 39, 54, 58, 39, 91, 58, 96, 11, 41, 56, 60, 53, 92, 83, 97, 17, 45, 67, 71, 45, 94, 71, 98, 23, 47, 69, 73, 66, 95, 87, 99, 11, 53, 56, 83, 41, 92, 60, 97, 29, 60, 77, 85, 60, 97, 85, 100, 23, 66, 69, 87, 47, 95, 73, 99, 35, 73, 81, 89, 73, 99, 89, 101];

ntca2rca = [[0], [1, 4, 64, 256], [2, 8, 32, 128], [3, 6, 9, 36, 72, 192, 288, 384], [5, 65, 260, 320], [7, 73, 292, 448], [10, 34, 136, 160], [11, 38, 200, 416], [12, 33, 66, 96, 129, 132, 258, 264], [13, 37, 67, 193, 262, 328, 352, 388], [14, 35, 74, 137, 164, 224, 290, 392], [15, 39, 75, 201, 294, 420, 456, 480], [16], [17, 20, 80, 272], [18, 24, 48, 144], [19, 22, 25, 52, 88, 208, 304, 400], [21, 81, 276, 336], [23, 89, 308, 464], [26, 50, 152, 176], [27, 54, 216, 432], [28, 49, 82, 112, 145, 148, 274, 280], [29, 53, 83, 209, 278, 344, 368, 404], [30, 51, 90, 153, 180, 240, 306, 408], [31, 55, 91, 217, 310, 436, 472, 496], [40, 130], [41, 44, 104, 131, 134, 194, 296, 386], [42, 138, 162, 168], [43, 46, 139, 166, 202, 232, 418, 424], [45, 195, 360, 390], [47, 203, 422, 488], [56, 146], [57, 60, 120, 147, 150, 210, 312, 402], [58, 154, 178, 184], [59, 62, 155, 182, 218, 248, 434, 440], [61, 211, 376, 406], [63, 219, 438, 504], [68, 257], [69, 261, 321, 324], [70, 76, 100, 196, 259, 265, 289, 385], [71, 77, 263, 293, 329, 356, 449, 452], [78, 228, 291, 393], [79, 295, 457, 484], [84, 273], [85, 277, 337, 340], [86, 92, 116, 212, 275, 281, 305, 401], [87, 93, 279, 309, 345, 372, 465, 468], [94, 244, 307, 409], [95, 311, 473, 500], [97, 133, 268, 322], [98, 140, 161, 266], [99, 141, 165, 225, 270, 330, 354, 396], [101, 197, 269, 323, 326, 332, 353, 389], [102, 204, 267, 417], [103, 205, 271, 331, 358, 421, 460, 481], [105, 135, 300, 450], [106, 142, 163, 169, 172, 226, 298, 394], [107, 143, 167, 233, 302, 428, 458, 482], [108, 198, 297, 387], [109, 199, 301, 361, 364, 391, 451, 454], [110, 206, 230, 236, 299, 395, 419, 425], [111, 207, 303, 423, 459, 486, 489, 492], [113, 149, 284, 338], [114, 156, 177, 282], [115, 157, 181, 241, 286, 346, 370, 412], [117, 213, 285, 339, 342, 348, 369, 405], [118, 220, 283, 433], [119, 221, 287, 347, 374, 437, 476, 497], [121, 151, 316, 466], [122, 158, 179, 185, 188, 242, 314, 410], [123, 159, 183, 249, 318, 444, 474, 498], [124, 214, 313, 403], [125, 215, 317, 377, 380, 407, 467, 470], [126, 222, 246, 252, 315, 411, 435, 441], [127, 223, 319, 439, 475, 502, 505, 508], [170], [171, 174, 234, 426], [173, 227, 362, 398], [175, 235, 430, 490], [186], [187, 190, 250, 442], [189, 243, 378, 414], [191, 251, 446, 506], [229, 334, 355, 397], [231, 237, 363, 366, 399, 429, 462, 483], [238, 427], [239, 431, 491, 494], [245, 350, 371, 413], [247, 253, 379, 382, 415, 445, 478, 499], [254, 443], [255, 447, 507, 510], [325], [327, 333, 357, 453], [335, 359, 461, 485], [341], [343, 349, 373, 469], [351, 375, 477, 501], [365, 455], [367, 463, 487, 493], [381, 471], [383, 479, 503, 509], [495], [511]]

#### Testing 
# l = rca2ntca
# l = l.tolist() if not isinstance(l,list) else l
# assert ntca2rca==[[i for i,y in enumerate(l) if y==x]  for x in range(102)]


####
npmoore = np.reshape(range(9),(3,3,))
gollymoore = [
    [8,1,2],
    [7,0,3],
    [6,5,4]]
order_gollymoore = np.argsort(np.ravel(gollymoore))
tst = '012345678'
out = '412587630'
assert np.take(npmoore.ravel(),order_gollymoore).tolist()  == map(int,out)


henseldict={'0': ['_'],
 '1': ['c', 'e'],
 '2': ['a', 'c', 'e', 'k', 'i', 'n'],
 '3': ['i', 'a', 'n', 'j', 'r', 'e', 'c', 'q', 'y', 'k'],
 '4': ['a', 'r', 'i', 'n', 'w', 'k', 'y', 'q', 't', 'j', 'z', 'e', 'c'],
 '5': ['i', 'a', 'j', 'n', 'r', 'q', 'c', 'y', 'k', 'e'],
 '6': ['a', 'c', 'k', 'n', 'e', 'i'],
 '7': ['c', 'e'],
 '8': ['_']}


rca2ntca=np.array(rca2ntca,np.int);
henselidx={k: v for v, k in enumerate(hensellist)};
subconf='_cekainyqjrtwz';
p_NOTnumletter = re.compile(r'[^\da-zA-Z\-]')    

try:
    from data import *
    with open('tp','rb') as f:  # Python 3: open(..., 'rb')
       hdist, tst_data = pickle.load(f)
       hdist = np.array(hdist).reshape([512,512]);
except:
    print('[WARN]Not finding data.py')



def ntca2moore(binstr):
    '''
    102-bit ntCA bitstring --> 512-bit mooreCA bitstring
    '''
    out = [None]*512
    for i,res in enumerate(binstr):
        for j in ntca2rca[i]:
            out[j] = res
    return ''.join(out)
def table_variable_moore(s):
    '''
    List dummy variables (x8)
    And concatenate to the input string
    Useful for ruletables
    '''
    for i in range(8):
            s += '''
var a%d={0,2} ### curr0
var b%d={1,3} ### curr1'''%(i,i)
    s+='\n'
    return s

def flat2dict(lst):
    '''
    Group duplicate objects 
    '''
    d = {}
    for i,val in enumerate(lst):
        d[val] = d.get(val,[]) + [i]
    return d
def appendIndex(lst):
    '''
    Add index to duplicated objects
    '''
    d  = flat2dict(lst)
    out = len(lst)* [None]
    for k,pos in d.items():
        vals = ['%s%d'%(k,i) for i in range(len(pos))]
        for i,v in zip(pos,vals):
            out[i]=v
    return out
if __name__=='__main__':
    IN = ['a','b','a','a','b']
    print IN
    print addIndex(IN)


def invert(s):
    num = s[0]
    conf = henseldict[num]
    return ''.join([num]+[x for x in conf if x not in s])

def ntuple(lst,n):
    """ntuple([0,3,4,10,2,3], 2) => [(0,3), (4,10), (2,3)]
    
    Group a list into consecutive n-tuples. Incomplete tuples are
    discarded e.g.
    
    >>> group(range(10), 3)
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    """    
    return zip(*[lst[i::n] for i in range(n)])

def add_all(s,prime,sold,neg=0):
    for c in subconf:
        conf=prime+sold+c;
        try:
            s[henselidx[conf]]=str(1-neg);
        except KeyError:
            pass

    
class kb_2dtca():
#     def rulestr2alias(rulestr):
#         r=base2bin(int(rulestr),18,2);
#         r=r[:1:-1];
#         r+='0'*(18-len(r));
#         rule=[i for x,i in zip(r,range(len(r))) if x=='1'];
#         alias='b';
#         ps=1;
#         for a in rule:
#             if a>8 and ps:
#                 alias+='s';
#                 ps=0;
#             alias+=str((a)%9)
#         if ps==1:
#             alias+='s';
#         return alias        
    def alias2rulestr(self, ali):
        rule=['0']*18;
        ali=ali.replace('/','').lower().lstrip('b');
        (b,s)=ali.split('s');
        lst=list(str(int(i)+9) for i in s);
        bs=list(b)+(lst)
        for i in bs:
            rule[int(i)]='1';
        rnum=(''.join(rule[::-1]),2);
        return(rnum);
    def rulestr2adv(self,rulestr):
        #take an numpy array and convolution across the axis=[1,2];
        # project the convolved array back to value space according to the rule
        # 
        hex2bin(rulestr)
                                       
class CA_sys():
    def __init__(self,familyname = None,rulestr=None,alias=None,dimsiz=None,adv=None,rdf=None):
#         siz=[600,100,400];
        if dimsiz is None:
            dimsiz = [128,128,32**2]
        if familyname is None:
            familyname = '2dntca'
        self.familyname=familyname;
        self.family=eval('kb_%s()'%self.familyname);
        if alias is None:
            if rulestr is None:
                rulestr = {'2dntca':'0c83820e0060061941946a68f0',
                          'eca':'01110110', #### rule 110
                          }.get(self.familyname,'I dont know the rulestring')
            self.rulestr = rulestr
            self.rulestr2alias()
            pass
        else:
            self.alias = alias
            self.alias2rulestr()
            pass
        self.alias = alias
        self.adv=adv;
        self.dimsiz=dimsiz;
        self.change_size();
#         self.family = globals().get('familyname')
#         self.
        if rdf==None:
#            self.rdf=lambda:(np.random.random(self.siz)<=0.5).astype(np.int);
            self.rdf = lambda p=0.5:(np.random.random(self.siz)<=p).astype(np.int);
            
    def change_size(self,dimsiz=None):
        if dimsiz==None:
            dimsiz=self.dimsiz;
        N,hmax,ksq=dimsiz
        self.N=N;
        self.hmax=hmax;
        dd=int(ksq**0.5);
        self.siz = (N,dd,dd);
        
    def rulestr2alias(self):
#         kb=eval('kb_%s()'%self.familyname);
        # kb=eval('kb_%s'%self.familyname);
        self.alias=self.family.rulestr2alias(self.rulestr);
        self.adv=self.family.rulestr2adv(self.rulestr);
    def alias2rulestr(self):
#         kb=eval('kb_%s()'%self.familyname);
        # kb=eval('kb_%s'%self.familyname);
        self.rulestr=self.family.alias2rulestr(self.alias)
        self.adv    =self.family.rulestr2adv(self.rulestr)            
    def as_config(self):
        conf = {'family':self.family.familyname,
               'rulestr':self.rulestr,
                'alias':self.alias,}
        return conf
#     def change_adv(familyname,rulestr):



    
# @function

# @function
def measure_temperature(sys0=None,hdist=None,*args,**kwargs):
#     varargin = measure_temperature.varargin
#     nargin = measure_temperature.nargin
    sysX=copy.copy(sys0)
    jmax=sysX.N;
    avi=sysX.rdf().astype(np.int)
    siz=avi.shape
    siz=(sysX.hmax,)+siz;
    tmp=np.zeros(siz)
    smtmp=np.zeros(siz)

    avc=avi
    i=0
    fir=np.reshape(2 ** (np.arange(0,9)),[1,3,3])
    trans=6
    mtp=0
    stp=0
    while i+1 < sysX.hmax:

        i=i + 1
        avcnew=(sysX.adv(avc,i))
        cavc=convolve_int(avc,fir,'wrap').astype(np.int);
        cavcnew=convolve_int(avcnew,fir,'wrap').astype(np.int);
        idx=np.ravel_multi_index((cavc,cavcnew),[2**9,2**9]);
        tmp[i,:,:,:]=np.expand_dims(hdist.flat[idx],0)
        if i >= trans:
            smtmpnow=np.mean(tmp[i - trans:i,:,:,:],axis=0)
            smtmp[i - trans,:,:,:]=smtmpnow
            if i >= trans + 10:
                mtp=np.mean(smtmpnow.flat)
                stpmat=((smtmp[i - trans,:,:,:] - smtmp[i - trans - trans,:,:,:]))
                a=np.mean(np.abs(stpmat.flat))
                b=abs(np.mean(stpmat.flat))
                stp=a - b
                stp1=np.mean(avcnew.flat)
                stp1=min(stp1,1 - stp1)
        avc=avcnew;
        #     im1=[avc(1,:,:)];
        if mtp < 0.02 and i > 20:
            break
    
    fam_alias=sys0.familyname+'_'+sys0.alias;
# /home/shouldsee/Documents/repos/CA_tfmat/custom_function/measure_temperature.m:55
    # s=sprintf('%s\\t%s\\t%d\\t%f\\t%f\\t%f\\n',fam_alias,num2str(sys0.od),i,mtp,stp,stp1)
    s='{}\t{}\t{:d}\t{:f}\t{:f}\t{:f}\n'.format(fam_alias,sysX.rulestr,i,mtp,stp,stp1)
# /home/shouldsee/Documents/repos/CA_tfmat/custom_function/measure_temperature.m:56
    return s
    
# if __name__ == '__main__':
#     pass
    


### Profiling loop
### Profiling loop
def profile(input_list, log = []):
    # global log
    output_data=[];    
    repeat=2;
    # input_list=[input_rulestr];
    ipt_list=input_list*repeat;
    # for i in range(5):
    l_ipt=len(input_list)
    log += ['Log of the process:'];
    logs='Starting to profile {:d} rules at {:d} replicates,\n totaling {:d} instances'.format(l_ipt,repeat,l_ipt*repeat);
    log += [logs];
    # print('Starting to profile {:d} rules at {:d} replicates,\n totaling {:d} instances'.format(l_ipt,repeat,l_ipt*repeat))

    for num,rulestr in enumerate(ipt_list):
        ca1=CA_sys(familyname,rulestr,[400,100,400]);
        ca1.rulestr2alias();
        s=measure_temperature(ca1,hdist);
        output_data+=[s];
    #     print('{:d} of {:d}'.format(num,len(ipt_list)))
        logs =('{:d} of {:d} '.format(num,len(ipt_list)));
        log += [logs];
    temp_data=[];
    # sample_data=[]
    for line in output_data:
        temp_data+=[line.rstrip('\n').split('\t')];
    sample_data=np.array(temp_data)
    # print('data is succesfully generated at {:d} replicates'.format(repeat))
    logs=('data is succesfully generated at {:d} replicates'.format(repeat))

    log  += [logs];

    # print('\n Detail of the input:')
    logs='\n Detail of the input:';
    log+=[logs];
    for k,v in ca1.__dict__.items():
        if not callable(v):
    #         print(k+str(v).ljust(-10))
    #         print("{:5} {:<15} {:<10}".format('',k, str(v)))

            logs=("{:5} {:<15} {:<10}".format('',k, str(v)));
            log+=[logs];
    return( [sample_data,log]);
    
if __name__ == '__main__':
    INPUT = "B345678/S012678"
    exp = "3f9fbe3e001fff07e07e15fea0"
    act = kb.alias2rulestr(INPUT)
    assert act == exp,'expected:%s, actual:%s' %(exp,act)
#     pass

def guess(i=None,sysX=None,dct=None):
    dimsiz = (256,2**7,24**2)
    if i is not None:
        rstr = tst_data[i][1]
        familyname='2dntca'
    if dct is not None:
        familyname = dct['family']
        rstr = dct['rulestr']
    if sysX is None:
        sysX = CA_sys(familyname,rstr,dimsiz)
        # sysX = KBs.CA_sys('2dntca',tst_data[i][1],(200,2**7,400))
        sysX.rulestr2alias()
    else:
        sysX.dimsiz = dimsiz
        sysX.change_size()# spspa.distance
    return sysX


import IPython.display as ipd
def lview(self):
    fmt = 'http://newflaw.com/view.php?rule_alias={:}'
    uri = fmt.format(self.alias)
    print uri
    ele = '<iframe src="{}" width=600 height=500></iframe>'.format(uri)
    ipd.display(ipd.HTML(ele))
    return uri


# def sample(self,ini=None,adv = None):
#     '''
#     Sample an iterator ('CA_sys' object)
#     '''
#     if adv is None:
#         adv = self.adv
#     if ini is None:
#         ini=self.rdf().astype(int)
#     avc = ini
#     hist = np.zeros((self.hmax,)+avc.shape,dtype=np.int)
#     for i in range(self.hmax):
#         hist[i]=avc
#         avc=(adv(avc)) 
#     return hist

def fill_ber(arr,p=0.5):
    '''
    Create bernouli using shape of arr
    '''
    return np.random.random(arr.shape) < p
def mix_adv(fA,fB,pa=0):
    '''
    Mixing two iterator
    '''
    if pa==1:
        adv = lambda arr:fA(arr)
    elif pa==0:
        adv = lambda arr:fB(arr)
    else:
        def adv(arr):
            mask = np.random.random(arr.shape)<pa
            A = fA(arr)
            B = fB(arr)
#             arr[mask] = A
#             arr[~mask] = B
            out = A*mask + B*(1-mask)
            return out
#             return arr
    return adv
def cov2cor(COV):
    D = np.diag(COV)
    COR = COV /  np.sqrt(D[:,None]*D[None,:])
    return COR


# Fast run length encoding
def rle (img):
    '''
    Source:https://www.kaggle.com/hackerpoet/even-faster-run-length-encoder
    '''
    x = np.ravel(img)
#     flat_img = img.flatten()
#     flat_img = np.where(flat_img > 0.5, 1, 0).astype(np.uint8)
    ### startswith 0->1
    ### endswith 1->0
    starts = np.array((x[:-1] == 0) & (x[1:] == 1))
    ends = np.array((x[:-1] == 1) & (x[1:] == 0))
    starts_ix = np.where(starts)[0] + 1
    ends_ix = np.where(ends)[0] + 1
    if x[0] == 1:
        starts_ix = np.insert(starts_ix,0,0)
    if x[-1] == 1:
        ends_ix = np.append(ends_ix,len(x))
    lengths = ends_ix - starts_ix
    
    return starts_ix, lengths
def _gollyrle(x):
    sl = rle(x)
    sym='bo$'
    S = 0
    out = ''
    L = 0
#     if s
    if sl[0].size!=0:
        for s,l1 in zip(*sl):
            l0 = s-S-L
            if l0>0:        
                inc = '%d%s'%(l0,sym[0]) ### number of zeros
                out = '%s%s'%(out,inc)
            inc = '%d%s'%(l1,sym[1])
            out = '%s%s'%(out,inc)
            S = s
            L = l1
    l0 = len(x)-S-L
    if l0>0:        
        inc = '%d%s'%(l0,sym[0]) ### number of zeros
        out = '%s%s'%(out,inc)
#     out='%s%s'%(out,sym[-1])
    return out
_gollyrle(map(int,list('010001001010')))
def gollyrle(arr):
    return '$'.join(map(_gollyrle,arr))
def hill(x):
    return 1-abs(2*x-1)
def sflatten(arr):
    return np.reshape(arr,(len(arr),-1))
def sexpand(arr,d=2):
    S = arr.shape
    root = int(round(S[1]**(1./d)) )
    out = np.reshape(arr,(S[0],)+(root,)*d)
    return out


def showsptime(arr,ax=None,**kwargs):
    if ax is None:
        fig,ax = plt.subplots(1,1,figsize=[12,4])    
    return ax.pcolormesh(sflatten(arr),**kwargs)


class kb_2dntca(object):
    familyname='2dntca'
    def __init__(self):
        #self.familyname='2dntca'
        pass
    def rulestr2alias(self, rulestr):
        '''
        Convert a 26-digit hexadecimal rulestring to a B/S alias
        '''
        OUT = ''
        # rulestr =  '000000000060031c61c67f86a0'
        r=hex2bin(rulestr,102);
        r=r[::-1];
        rule=[i for i,x in enumerate(r) if x=='1'];
#         print r
        lst = [hensellist[i] for i in rule]
        lst.sort()
        
        #### group by B/S
        d = collections.OrderedDict((('b',{}),('s',{}))) ### set default
#         d = {'b':{},'s':{}}   ### set default
        d.update(
            {k:list(gp) for k,gp in itertools.groupby(lst, lambda x:x[0])}        
        )
        for k,lst in d.items():
            d[k] = {k:list(gp) for k,gp in itertools.groupby(lst, lambda x:x[1])}
            
        for bs, dd in d.items():
            OUT += bs
            for k,lst in dd.items():
                OUT += k + ''.join( conf[-1] for conf in lst)
        OUT = OUT.replace('_','')
        alias = OUT
        return alias


    def alias2rulestr(self,alias): 
        '''
        Convert a B/S alias to a 26-digit hexadecimal rulestring
        '''
    # alias.replace('-','')
        alias = re.sub('(\d-[a-zA-Z]+)',lambda o:invert(o.group()),alias)
        alias = p_NOTnumletter.sub( '', alias).lower()
        OUT = ['0']*102
        d = collections.OrderedDict((('b',{}),('s',{}))) ### set default
        # d.update()
        # alias.split('s')
        s = alias
        lst = [x for x  in re.split("([bs])", s) if x]
        if len(lst) % 2: #### Padding to even length
            lst += ['']
        d  = dict(ntuple(lst,2))
        idxs = []
        for k, v in d.items():
            s = v
            lst = [x for x in re.split("(\d)", s) if x]
            L  = len(lst)
            v_old = ''
            for i,v in enumerate(lst):
                if v.isdigit():
                    if v_old.isdigit():
                        idx = [henselidx.get( k + v_old + c,None) for c in subconf]
                        idxs.extend(idx)
                    if i + 1 == L:
                        idx = [henselidx.get( k + v + c,None) for c in subconf]
                        idxs.extend(idx)
                    num = v
                else:
                    idx = [henselidx[ k + num + v_i]  for v_i in v ]
                    idxs.extend(idx)
                v_old = v
        idxs = [ x for x in idxs if x is not None] 
        for i in idxs:
            if not i is None:
                OUT[i] = '1'
        bitstr=''.join(OUT[::-1]);
        hexstr=hex(int(bitstr,2)).lstrip('0x').rstrip('L').zfill(26)
        return hexstr
    def rulestr2adv(self,rulestr):
        ruleprj=np.array( 
            list(hex2bin(rulestr,102)[::-1]),
            np.int);
        adv = self.bin2adv(ruleprj)
        return adv 
    def conv(self,IN):
        '''
        Convovle using non-totalistic isotropic filter
        '''
        fir=(2**np.arange(0,9)).reshape([1,3,3]);
        pj=rca2ntca;
        return pj[convolve_int(IN,fir,'wrap').astype(np.int)]
    def bin2adv(self, ruleprj):
        if isinstance(ruleprj,str):
            ruleprj = list(ruleprj)
        ruleprj = np.array(ruleprj,np.int)
        def adv(a,horizon=0):
            return ruleprj[self.conv(a)]
        return adv
    def rstr(self,callback=(lambda x:bin2hex(x).zfill(26)) ):
        r = '{:0102b}'.format(random.randrange(2**102))
        if callback is not None:
            r = callback(r)
        return r
    def randadv(self):
        return self.bin2adv(self.rstr(None))
    def bulk_rstr(self,seed = 0,bsize=2**18,**kwargs):
        random.seed(seed)
        lst = [{'family':self.familyname,
                'rulestr':self.rstr(**kwargs)} for x in range(bsize)]
        return lst
    def rulestr2table(self,rstr):
        s = '''@RULE {alias:}
@TABLE
n_States:2
neighborhood:Moore
symmetries:rotate4reflect
'''.format(alias=self.rulestr2alias(rstr))
        binstr=hex2bin(rstr,102)[::-1]
        for i,bit in enumerate(binstr):
    #         if bit is '1':
            conf = base2bin(str(ntca2rca[i]),10,9)            
            conf = np.take(list(conf),order_gollymoore)
            line = ''.join(conf.tolist()+[bit])
    #             conf = ''.join([conf[order_gollymoore[x]] for x in range(len(conf))])
    #         print conf
            s+='%s\n'%line
        return s    
    def rulestr2table(self,rstr,reverse=0):
        nState = 4 if reverse else 2
        alias = self.rulestr2alias(rstr)
        if reverse:
            alias = 'rev_%s'%alias
        s = '''@RULE {alias:}
@TABLE
n_States:{nState}
neighborhood:Moore
symmetries:rotate4reflect
'''.format(alias=alias,
              nState=nState)
        if reverse:
            s=table_variable_moore(s)
        s += '#>>>TAB<<<\n'

        d = {'0':'a','1':'b'}
        binstr=hex2bin(rstr,102)[::-1]
        for i,bit in enumerate(binstr):
            conf = base2bin(str(ntca2rca[i][0]),10,9)            
            conf = np.take(list(conf),order_gollymoore).tolist()
            if not reverse:
                line = ''.join(conf+[bit])
                s+='%s\n'%line
            else:       
                c_cur = int(conf[0])

                for c_his in [0,1]:
    #                 print c_cur+2*c_his
                    #### Use history and proposed bit to calculate next state
                    c_nex = int(bit) ^ int(c_his)  
                    var = [d.get(x) for x in conf[1:]]

                    lst = [str(c_cur+2*c_his)] + appendIndex(var) +[str(c_nex+2*c_cur)]
                    line = ','.join(  lst)
                    s+='%s\n'%line
    #             line = conf
        return s    
    
class kb_eca(object):
    familyname='eca'
    def conv(self,IN,method):
        '''
        Convolve using 1D universal (non-totalistic non-isotropic) filter
        '''
        fir = (2**np.arange(3)).reshape([1,3,1])
        return convolve_int(IN,fir,method)
    def rstr(self,):
        pass
    def bin2adv(self,rulebin,method='wrap'):
        if isinstance(rulebin,str):
            rulebin = list(rulebin)
        rulebin = np.array(rulebin,np.int)
        def adv(a,horizon=0,method=method):
            return rulebin[self.conv(a,method=method)]
        return adv
    def rulestr2alias(self,rstr):
        assert len(rstr)==8,'rulestring=%s'%rstr
        alias = int(rstr,2)
        return str(alias)
    def alias2rulestr(self,alias):
        rstr = base2bin(alias,10,8)[::-1]
        return rstr
    def rulestr2adv(self,rstr):
        return self.bin2adv(rstr)
#### Testing kb_eca functionality
if __name__=='__main__':
    kb  = kb_eca()
    rstr = '11001010'
    alias = kb.rulestr2alias(rstr)
    print 'alias of mapper %s:'%rstr,alias
    print 'rulestring of rule 110:',kb.alias2rulestr('110')

    
    kb=kb_2dntca();
    # kb.rulestr2alias('000000000060031c61c67f86a0')
    kb.alias2rulestr('b3/s23')

# def sample(self,ini=None,adv = None,T = None):
#     '''
#     Sample an iterator ('CA_sys' object)
#     '''
#     if T is None:
#         T = self.hmax
#     if adv is None:
#         adv = self.adv
#     if ini is None:
#         ini=self.rdf().astype(int)
#     avc = ini
#     hist = np.zeros((T+1,)+avc.shape,dtype=np.int)
#     for i in range(T+1):
#         hist[i]=avc
#         avc=(adv(avc)) 
#     return hist
def showsptime(arr,ax=None,**kwargs):
    if ax is None:
        fig,ax = plt.subplots(1,1,figsize=[12,4])   
    return ax.pcolormesh(sflatten(arr),**kwargs)

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import IPython.display as ipd
def animate(arr,html = 1,nFrame=20):
    '''
    Animate a list of 2d-array
    '''
    fig, ax = plt.subplots()
    im = ax.imshow(arr[0])
    ax.grid()
    data_gen = arr

    def run(data):
        im.set_data(data)
        return im,

    ani = animation.FuncAnimation(fig, run, 
                                  data_gen, 
                                  blit=False,
                                  interval=1000./nFrame,
                                  repeat=1, init_func=None)
    plt.close()
    if html:
        ani = ipd.HTML(ani.to_html5_video())
    return ani

def sample(self,t=None,ini=None,adv = None,T = None):    
    '''
    Sample an iterator ('CA_sys' object)
    '''
    if t is None:
        t = {'r2dntca':2,}.get(self.family.familyname,1)
    if T is None:
        T = self.hmax
    if adv is None:
        adv = self.adv
    if ini is None:
        if t>=2:
            ini = np.array([self.rdf().astype(int)]*t)
        else:
            ini=self.rdf().astype(int)
    avc = ini
    hist = np.zeros((T+1+t-1,)+avc.shape[-3:],dtype=np.int)
    
    ###### !!!Be very careful with the indexing in this loop!!!
    for i in range(0,T+1):
        hist[i] = avc[0] if t>=2 else avc
        avc=(adv(avc)) 
    return hist

class kb_r2dntca(kb_2dntca):
    '''
    Reversible 2dntca
    '''
    familyname='r2dntca'

    def bin2adv(self, ruleprj):
        if isinstance(ruleprj,str):
            ruleprj = list(ruleprj)
        ruleprj = np.array(ruleprj,np.int)
        def adv(a,horizon=0):
            old = a[0]
            curr = a[1]
            new  = ruleprj[self.conv(curr)]^old
            return np.array([curr,new])
                              
        return adv

        
