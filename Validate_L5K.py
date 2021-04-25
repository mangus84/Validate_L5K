# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 22:48:46 2021

@author: mangus
"""

import re
import time, os


class Segment:
    '''
    Class object for segment type of *.L5K file file PROGRAM, ROUTINE, TAG etc.
    Arguments
    ---------
    s_header: string      - header defining start of segment i.e. PROGRAM     
    e_header: string      - header defining end of segment i.e. END_PROGRAM
    line:     string      - current line of project's file to be checked
    chck:     bool        - check project file lines for tags (after s_header
                                                               found)
    save:     bool        - save results of the check (when e_header found)
    segments: dict        - result of the check of whole segment dictionary 
                            of segment element name (key) and dictionary of
                            found tags (value - dictionary of line number and
                                        tag name)
    name:     string      - name of the current segment element
    lnNo:     int         - line number to save found tag's position
    
    
    Methods
    -------
    chck_header
    get_name
    seg_chck
    seg_save    
    '''
    
    
    def __init__(self, s_header, e_header):
        self.s_header = s_header
        self.e_header = e_header
        self.line = ''
        self.chck = False
        self.save = False
        self.segments = {}
        self.name = ''
        self.lnNo = 0
        
        
    def chck_header(self, header, line):
        '''
        Checking if given header is present. 
        Only white space before the header in the line
        Parameters
        ----------
        line :  string      - current file line
        header: string      - header to look for in the line
        
        Returns
        -------
        condition: boolean  - header present and only white space before it
        '''

        self.header_pos = line.find(header)       
        self.wSpace = line[:self.header_pos].isspace()                                
        return self.header_pos == 0 or (self.header_pos != -1 and self.wSpace)                     #check routine's header and only whitespace before it    


    def get_name(self, line):
        '''
        Extract the name of found segment element
        Parameters
        ----------
        line :  string      - current file line
        '''
        
        head_start = line.find(self.s_header)
        head_end = head_start + len(self.s_header) + 1
        if line.find('(') != -1:                                               #check "(" after header name
            self.name = line[head_end:line.find('(')-1]                             #slice out header's name 
        else:
            temp_pos = line[head_end:].find(' ')
            self.name = line[head_end:head_end + temp_pos]                          #slice out header's name    


    def seg_chck(self, line):
        '''
        If starting header found and not previously set to check than set check
        bit
        Parameters
        ----------
        line :  string      - current file line
        '''
        
        if self.chck_header(self.s_header, line) and not self.chck:         
            self.lnNo = 0
            self.get_name(line)                
            self.chck = True                                                        #set flag to check each routine line/rung
   
    
    def seg_save(self, line):
        '''
        If end header found and not previously set save bit - save check
        results
        Parameters
        ----------
        line :  string      - current file line
        ''' 
        
        self.save = False         
        if self.chck_header(self.e_header, line):
            self.chck = False                                                       #reset flag to check each routine line/rung
            self.save = True                                                        #set flag to save result of the routine check     
        

def get_tags_from_rung(line):
    '''
    Extracts tags' names from the given text line/rung.
    Tags are included in the line with parenthesis: (tagname)
    Parameters
    ----------
    line : string - line of text to extract tags from
    
    Returns
    -------
    tags_list : list of strings - all tags' names found in the line
    '''
    
    tags_list = []
    
    while line.find('(') != -1:                                                 #is any tag in the line        
        tag = line[line.find('(')+1:line.find(')')]                                 #extract tag's name using string slicing   
        tags_list.append(tag)                                                       #add to the list of rung's tags
        line = line[line.find(')')+1:]                                              #remove extracted tag from analyzed line
    
    return tags_list


def filter_tags(tags_list, tag_name):
    '''
    Loops given tag list through to find any occurance of given tag name pattern.
    I.e.: if we look for "shunt" tags any 'gp_shunt.1' etc. will be found
    Returns list of found tags full name.
    Parameters
    ----------
    tags_list :  list of strings - list of tags to check
    tag_name:    string          - name pattern to look for
    
    Returns
    -------
    found_tags: list of string  - list of full names of tags matching the pattern
    '''
    
    found_tags = []
    
    for tag in tags_list:
        # if tag.find(tag_name) != -1:
        #     found_tags.append(tag)
        if re.search(tag_name, tag, re.IGNORECASE):
            found_tags.append(tag)
    return found_tags


def validate_proj(project, tag_pattern):
    '''
    Function to validate *.L5K project against specific tag usage 
    like ('shunt', 'test' etc.)
    Parameters
    ----------
    project :     file          - *.L5K file to be validated
    tag_patter:   string        - tag name pattern to look for
    
    Returns
    -------
    segments:     dict          - structure of dictionaries and lists of
                                  strings containing validation results
    '''
      
    Program = Segment('PROGRAM', 'END_PROGRAM')                                     
    Routine = Segment('ROUTINE', 'END_ROUTINE')
    
    '''
    *.L5K file structure to verify looks like:
        PROGRAM xyz
            ROUTINE xyz
            END_ROUTINE
            
            ROUTINE zxy
            END_ROUTINE zxy
        END_PROGRAM
    '''
    
    pattern_pos = {}
    file_line = ''
    
    for file_line in project_file:
        Program.seg_chck(file_line)
        Program.seg_save(file_line)
            
        if Program.chck:
            Routine.seg_chck(file_line)
            Routine.seg_save(file_line)   
            
                
            if Routine.chck_header('N:', file_line) and Routine.chck:            
                tags_in_rung = get_tags_from_rung(file_line)                            #get names of all tags in the rung        
                pattern_in_rung = filter_tags(tags_in_rung, tag_pattern)                     #check for shunts
        
                if pattern_in_rung != []:
                    pattern_pos[Routine.lnNo] = pattern_in_rung
                Routine.lnNo += 1
                
            if Routine.save:
                Routine.segments[Routine.name] = pattern_pos
                pattern_pos = {}
        
        if Program.save:
            Program.segments[Program.name] = Routine.segments
            Routine.segments = {}  
            
    return Program.segments


def disp_results(segments):
    '''
    Displays results of project validation.
    Parameters
    ----------
    segments:     dict          - structure of dictionaries and lists of
                                  strings containing validation results
    '''
    
    for program in segments:                                                    #go all program through
      print('Program: %s' % program)
      for routine, rungs in segments[program].items():                          #for every prorgam go all routines (keys) and their rungs (values as dictionaries) through
          print('\tRoutine: %s' % routine)
          for rung, shunts in rungs.items():                                    #display last nested item - dictonairy rung (key - integer) and shunt/tags list (value - list of strings)
              print('\t\tRung #%d: ' % rung, end ='')
              for shunt in shunts:
                  print('%s, ' % shunt, end ='')
              print('')   
           
            
def save_results(segments, file):
    '''
    Writes results of project validatin into a *.txt file. Name of the file
    consists of the project file name with '_results' suffix.
    Parameters
    ----------
    segments:     dict          - structure of dictionaries and lists of
                                  strings containing validation results
    file:         string        - name of validated project file
    '''
    
    file_name = file[:file.find('.')] + '_results.txt'                          #Builds name of the results file
    with open(file_name, 'w') as result_file:
        for program in segments:                                                    #go all program through
          result_file.write('Program: %s \n' % program)
          for routine, rungs in segments[program].items():                          #for every prorgam go all routines (keys) and their rungs (values as dictionaries) through
              result_file.write('\tRoutine: %s \n' % routine)
              for rung, shunts in rungs.items():                                    #display last nested item - dictonairy rung (key - integer) and shunt/tags list (value - list of strings)
                  result_file.write('\t\tRung #%d: ' % rung)
                  for shunt in shunts:
                      result_file.write('%s, ' % shunt)
                  result_file.write('\n')   

#------------------------------------------------------------------------------
#Script execution
#------------------------------------------------------------------------------

path = os.getcwd() + '\Test_Projects'                                           #Current working directory (folder with script file) + name of the folder containing project files
print(path)
listOfFiles = os.listdir(path)                                                  #Get the list of project files
print(listOfFiles)                

        
t0 = time.time_ns()

os.chdir(path)                                                                  #Change working directory to the folder with project files to be validated
for file_name in listOfFiles:

    with open(file_name, 'r') as project_file:
        results = validate_proj(project_file, 'shunt')
#        disp_results(results)
        save_results(results, file_name)

            
t1 = time.time_ns()
t = (t1 - t0)/1000000
print('It took %.2f ms' %t)