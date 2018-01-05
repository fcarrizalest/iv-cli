# iv/commands/hello.py
"""The hello command."""

import os
import os.path as osp
import shutil
import logging
import tempfile
import configparser
import io
import tarfile
import ftputil
import errno,  stat, shutil

from json import dumps
from .base import Base
from git import Repo
from git import RemoteProgress

def handleRemoveReadonly(func, path, exc):
  excvalue = exc[1]
  if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
  else:
      raise

class MyProgressPrinter(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print( cur_count / (max_count or 100.0), message or "NO MESSAGE")
# end



class Deploy(Base):
    """Say hello, world!"""

    __configfile_name__ = "iv.ini"


    def uplodad(self):
        with ftputil.FTPHost(self.host , self.user, self.passwd ) as ftp_host:


            self.untar_path = os.path.join(  self.untar_path , *self.deploy_dir.split('/') )

            self.upload_dir( ftp_host , self.untar_path , self.dir   )

    def upload_dir(self, ftp_host,localDir, ftpDir):


        

       
        
        list = os.listdir(localDir)

        for fname in list:
            ftp_host.chdir(ftpDir)
            local_path_fname = os.path.join(localDir , fname)
            ftp_path_fname =  os.path.join(ftpDir , fname)
            if os.path.isdir( local_path_fname ):

                if(ftp_host.path.exists( fname  ) != True):
                    print(ftp_path_fname)
                    ftp_host.mkdir( fname )
                    print( fname  + " is created.")

                ftp_host.chdir(fname)

                self.upload_dir(ftp_host,local_path_fname , ftp_host.getcwd() )
            else:
                if(ftp_host.upload_if_newer(local_path_fname, fname )):
                    print( local_path_fname  + " is uploaded.")
                else:
                    print( local_path_fname + " has already been uploaded.")

    def untar_file(self):
        self.untar_path = tempfile.mkdtemp()

        tar = tarfile.open(self.tar_file)
        tar.extractall( path= self.untar_path  )
        tar.close()



    def parse_ini_config(self):

        ftp_key = 'ftp'
        deploy_key = 'deploy'

        config = configparser.ConfigParser()

        config.read(self.__configfile_name__)


        self.deploy_dir = '/'

        if config.has_section(deploy_key):
            self.deploy_dir = config.get(deploy_key,'dir')



        if config.has_section(ftp_key) :

            self.host = config.get(ftp_key,'host')
            self.user = config.get(ftp_key,'user')
            self.passwd = config.get(ftp_key,'passwd')
            self.dir = config.get(ftp_key,'dir')


    def info(self):
        repo = Repo(os.getcwd())

        print( 'Path:' + os.getcwd() )

        for remote in repo.remotes:

            print( 'Remote: ' + str(remote)  ) 



        for ref in repo.references:

            print( ref.name )


        print('FTP')
        self.parse_ini_config()

        print( "Ftp Host: %s" %  self.host )
        print( "Ftp User: %s" %  self.user ) 
        print( "Ftp Pass: %s" % self.passwd )
        print( "Ftp Dir: %s " % self.dir )

        with ftputil.FTPHost(self.host , self.user, self.passwd ) as ftp_host:
            print('Conection success')






    def download_repo(self):
        buildPath = tempfile.mkdtemp()
        self.buildPath = buildPath
        print( buildPath )
        tar_file = tempfile.mkdtemp()

        self.dir_tar_file = tar_file

        tar_file = os.path.join(tar_file , 'deploy.tar')

        self.tar_file = tar_file

        print( tar_file  )

        repo = Repo(os.getcwd())
        
        for url in repo.remotes[0].urls:

            cloned_repo = repo.clone_from( 
                    url , 
                    buildPath, 
                    progress=MyProgressPrinter() )

            hcommit = cloned_repo.head.commit
            for ref in repo.references:
                if ref.name ==  self.options['<brandname>'] :
                    archivos = []
                    for ar in hcommit.diff( ref.commit ):
                        print(ar)
                        if not ar.deleted_file:
                            archivos.append( str(ar.a_path) )
                    ref.checkout()
                    with open( tar_file  , 'wb') as fp:
                        cloned_repo.archive(fp ,treeish=ref, path = archivos )

            



    def delete_build(self):

        try:
            shutil.rmtree( self.buildPath  ,  ignore_errors=False, onerror=handleRemoveReadonly )
            shutil.rmtree( self.untar_path  ,  ignore_errors=False, onerror=handleRemoveReadonly)
        except Exception as e:
            pass

        


    def run(self):

        if self.options['info']:
            self.info()

            return None

        if self.options['init'] :
            cfgfile = open(self.__configfile_name__, 'w')
            Config = configparser.ConfigParser()
            Config.add_section('deploy')
            Config.set('deploy', 'dir', '/')


            Config.add_section('ftp')
            Config.set('ftp', 'host', '127.0.0.1')
            Config.set('ftp', 'user', 'root')
            Config.set('ftp', 'passwd', 'toor')
            Config.set('ftp', 'dir', '/')
            Config.write(cfgfile)
            cfgfile.close()


        if not os.path.isfile(self.__configfile_name__):
            print('config no found  iv deploy init ')
            return None


        if self.options['ftp']:
            self.parse_ini_config()
            self.download_repo()
            self.untar_file()
            self.uplodad()
            self.delete_build()
            
            







        return None


    	


       

        	

        

        # for diff_added in hcommit.diff('HEAD~1'):
        # 	print(diff_added)



