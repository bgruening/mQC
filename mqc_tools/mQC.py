#####################################
##	mQC (MappingQC): ribosome profiling mapping quality control tool
##  Author: S. Verbruggen
##  Supervised by: G. Menschaert
##
##	Copyright (C) 2017 S. Verbruggen & G. Menschaert
##
##	This program is free software: you can redistribute it and/or modify
##	it under the terms of the GNU General Public License as published by
##	the Free Software Foundation, either version 3 of the License, or
##	(at your option) any later version.
##
##	This program is distributed in the hope that it will be useful,
##	but WITHOUT ANY WARRANTY; without even the implied warranty of
##	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##	GNU General Public License for more details.
##
##	You should have received a copy of the GNU General Public License
##	along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
## 	For more (contact) information visit https://github.com/Biobix/mQC
#####################################


__author__ = 'Steven Verbruggen'

import traceback
import getopt
from collections import defaultdict
import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import hex2color
from matplotlib import cm
import seaborn as sns
from matplotlib.ticker import ScalarFormatter
import re
import time




'''

Make mappingQC plots

ARGUMENTS

    -w | --word_dir                         The working directory
                                                (default = current working directory)
    -s | --input_samfile                    The sam file used as input
                                                (default STAR/fastq1/untreat.sam)
    -e | --exp_name                         The name of the experiment
                                                (mandatory)
    -o | --outfolder                        The output directory
                                                (default workdir/mappingQC_output/)
    -h | --outhtml                          The output html file
                                                (default mQC.html)
    -z | --outzip                           The output zip file name
                                                (default mQC.zip)
    -p | --plastid_option                   Origin of offsets (plastid, standard or from_file)
                                                (default standard)
    -i | --plastid_img                      Path to the plastid offset image
                                                (mandatory if plastid option equals 'plastid')
    -e | --ensembl_db                       Ensembl database
                                                (mandatory)
    -v | --ensembl_version                  The Ensembl database version
                                                (mandatory)
    -u | --unique                           Use unique alignments (Y/N)
                                                (default Y)
    -x | --plotrpftool                      The tool to plot the RPF phase figure (grouped2D/pyplot3D/mayavi)
                                                (default: grouped2D)
    -t | --tmp_folder                       The temporary folder with temporary results
                                                (default work_dir/tmp)
    -d | --species                          Species
                                                (mandatory)
    -g | --galaxy                           Run on galaxy or not (Y/N)
                                                (default N)
    -a | --galaxysam                        Galaxy parameter (Y/N)
                                                (default Y)

EXAMPLE

python mQC.py -s STAR/fastq1/untreat.sam  -e ENS_hsa_86.db

'''

def main():

    # Catch command line with getopt
    try:
        myopts, args = getopt.getopt(sys.argv[1:], "w:s:n:o:h:z:p:i:e:v:u:x:t:d:g:a:", ["work_dir=", "input_samfile=", \
                        "exp_name=","outfolder=", "outhtml=", "outzip=", "plastid_option=", "plastid_img=" ,\
                        "ensembl_db=", "ensembl_version=", "unique=", "plotrpftool=" , "tmp_folder=", "species=", "galaxy=","galaxysam="])
    except getopt.GetoptError as err:
        print err
        sys.exit()

    # Catch arguments
    # o == option
    # a == argument passed to the o
    for o, a in myopts:
        if o in ('-w', '--work_dir'):
            workdir = a
        if o in ('-s', '--input_samfile'):
            samfile = a
        if o in ('-n','--exp_name'):
            exp_name = a
        if o in ('-o','--outfolder'):
            outfolder = a
        if o in ('-h', '--outhtml'):
            outhtml = a
        if o in ('-z', '--outzip'):
            outzip = a
        if o in ('-p', '--plastid_option'):
            plastid_option = a
        if o in ('-i', '--plastid_img'):
            plastid_img = a
        if o in ('-e', '--ensembl_db'):
            ens_db = a
        if o in ('-v', '--ensembl_version'):
            ens_version = a
        if o in ('-u', '--unique'):
            unique = a
        if o in ('-x', '--plotrpftool'):
            plotrpftool=a
        if o in ('-t', '--tmp_folder'):
            tmpfolder = a
        if o in ('-d', '--species'):
            species = a
        if o in ('-g', '--galaxy'):
            galaxy = a
        if o in ('-a', '--galaxysam'):
            galaxysam = a

    try:
        workdir
    except:
        workdir = ''
    try:
        samfile
    except:
        samfile = ''
    try:
        exp_name
    except:
        exp_name = ''
    try:
        outfolder
    except:
        outfolder = ''
    try:
        outhtml
    except:
        outhtml = ''
    try:
        outzip
    except:
        outzip = ''
    try:
        plastid_option
    except:
        plastid_option = ''
    try:
        plastid_img
    except:
        plastid_img = ''
    try:
        ens_db
    except:
        ens_db = ''
    try:
        ens_version
    except:
        ens_version = ''
    try:
        unique
    except:
        unique = ''
    try:
        plotrpftool
    except:
        plotrpftool = ''
    try:
        tmpfolder
    except:
        tmpfolder = ''
    try:
        species
    except:
        species = ''
    try:
        galaxy
    except:
        galaxy = ''
    try:
        galaxysam
    except:
        galaxysam = ''

    # Check for correct arguments and parse
    if galaxy == '':
        galaxy = 'N'
    else:
        if galaxy != 'N' and galaxy != 'Y':
            print "Error: galaxy option should be Y or N!"
            sys.exit()
    if galaxysam == '':
        galaxysam = 'Y'
    else:
        if galaxysam != 'N' and galaxysam != 'Y':
            print "Error: galaxysam option should be Y or N!"
            sys.exit()
    if workdir == '':
        workdir = os.getcwd()
    if workdir != '':
        os.chdir(workdir)
    if tmpfolder == '':
        tmpfolder = workdir+"/tmp"
    if samfile == '':
        samfile = "STAR/fastq1/untreat.sam"
    if exp_name == '':
        print "ERROR: do not forget the experiment name!"
        sys.exit()
    if outfolder == '':
        outfolder = workdir + "/mappingQC_output/"
    if outhtml == '':
        outhtml = workdir+"/mQC.html"
        outhtml_short = "mQC.html"
    else:  # only take the last part of the name
        backslash_test = re.search('/', outhtml)
        if backslash_test:
            m = re.search('.*/(.+?\.(html|dat))$', outhtml)
            if m:
                outhtml_short = m.group(1)
            else:
                print "Could not extract html file name out of given path ("+outhtml+")"
                sys.exit()
    if outzip == '':
        outzip = workdir+"/mQC.zip"
        outzip_short = "mQC.zip"
    else: # Only take the last part of the name
        backslash_test = re.search('/', outzip)
        if backslash_test:
            m = re.search('.*/(.+?\.(zip|dat))$', outzip)
            if m:
                outzip_short = m.group(1)
            else:
                print "Could not extract zip file name out of given path ("+outzip+")"
        else:
            outzip_short = outzip
    if plastid_option == '':
        plastid_option = 'standard'
    elif plastid_option != 'standard' and plastid_option != 'plastid' and plastid_option != 'from_file':
        print "ERROR: plastid option should be 'plastid', 'standard' or 'from_file'!"
        sys.exit()
    if plastid_option == 'plastid':
        if plastid_img == '':
            print "ERROR: do not forget to give path to plastid image if offset option equals 'plastid'!"
    if ens_db == '':
        print "ERROR: do not forget to mention the Ensembl db!"
        sys.exit()
    if ens_version == '':
        print "ERROR: do not forget to mention the Ensembl version!"
        sys.exit()
    if unique == '':
        unique = "Y"
    else:
        if unique != "Y" and unique != "N":
            print "ERROR: unique should be 'Y' or 'N'!"
            sys.exit()
    if plotrpftool == '':
        plotrpftool = "grouped2D"
    if species == '':
        print "ERROR: do not forget to mention the species!"
        sys.exit()

    ########
    # MAIN #
    ########

    # Make plots directory
    if not os.path.exists(outfolder):
        os.system("mkdir -p " + outfolder)

    # Download biobix image
    os.system("wget --quiet \"http://www.nxtgnt.ugent.be/images/img/logos/BIOBIX_logo.png\"")
    os.system("mv BIOBIX_logo.png " + outfolder)

    #Get plot data out of results DB
    phase_distr, total_phase_distr, triplet_distr = get_plot_data(tmpfolder)

    #Calculate number of alignments out of SAM file
    tot_maps = maps_out_of_sam(samfile, galaxy, galaxysam, tmpfolder)

    #Make total phase distribution plot
    outfile = outfolder+"/tot_phase.png"
    plot_total_phase(total_phase_distr, outfile)

    #Make RPF-phase distribution plot
    outfile = outfolder+"/rpf_phase.png"
    if plotrpftool == "grouped2D":
        plot_rpf_phase_grouped2D(phase_distr, outfile)
    elif plotrpftool == "pyplot3D":
        plot_rpf_phase_pyplot3D(phase_distr, outfile)
    elif plotrpftool == "mayavi":
        plot_rpf_phase_mayavi(phase_distr, outfile)

    #Make phase position distribution
    phase_position_distr(tmpfolder, outfolder)

    #Make triplet identity plots
    triplet_plots(triplet_distr, outfolder)

    #Write to output html file
    offsets_file = tmpfolder+"/mappingqc/mappingqc_offsets.csv"
    # Copy offsets image to output folder
    offset_img = "offsets.png"
    if plastid_option=="plastid":
        os.system("cp " + plastid_img + " " + outfolder + "/" + offset_img)
    #Copy metagenic pie charts to output folder
    tmp_rankedgenes = tmpfolder+"/mappingqc/rankedgenes.png"
    tmp_cumulative = tmpfolder+"/mappingqc/cumulative.png"
    tmp_density = tmpfolder+"/mappingqc/density.png"
    tmp_metagenic_plot_c = tmpfolder+"/mappingqc/annotation_coding.png"
    tmp_metagenic_plot_nc = tmpfolder+"/mappingqc/annotation_noncoding.png"
    os.system("cp "+tmp_cumulative+" "+outfolder)
    os.system("cp "+tmp_rankedgenes+" "+outfolder)
    os.system("cp "+tmp_density+" "+outfolder)
    os.system("cp "+tmp_metagenic_plot_c+" "+outfolder)
    os.system("cp "+tmp_metagenic_plot_nc+" "+outfolder)
    #Write output HTML file
    write_out_html(outhtml, outfolder, samfile, exp_name, tot_maps, plastid_option, offsets_file, offset_img,\
                   ens_version, species, ens_db, unique)

    ##Archive and collect output
    #Make output archive
    output_arch = "mQC_archive/"
    #Try to fetch alternative name out of zip file name
    m = re.search('(.+)\.zip$', outzip_short)
    if m:
        output_arch = m.group(1)
    os.system("mkdir " + workdir + "/" + output_arch)
    #Bring output html and output images folder to archive
    if galaxy=='Y':
        os.system("cp -r " + outhtml + " " + outfolder)
    else:
        os.system("mv " + outhtml + " " + outfolder)
    os.system("cp -r " + outfolder + " " + output_arch)
    #zip output archive
    tmpZip = workdir+"/tmp.zip"
    os.system("zip -r -q "+tmpZip+" "+output_arch)
    os.system("rm -rf " + output_arch)
    os.system("mv "+tmpZip+" "+outzip)


############
### SUBS ###
############

## Write output html file
def write_out_html(outfile, output_folder, samfile, run_name, totmaps, plastid, offsets_file, offsets_img,\
                   ensembl_version, species, ens_db, unique):

    #Load in offsets
    offsets = pd.read_csv(offsets_file, sep=',', header=None, names=["RPF", "offset"])
    max_rpf = offsets["RPF"].max()
    min_rpf = offsets["RPF"].min()
    html_table=""
    for ofs in range(min_rpf, max_rpf+1, 1):
        html_table += """<tr>
        <td>"""+str(ofs)+"""</td>
        <td>"""+str(int(offsets.loc[offsets["RPF"] == ofs]["offset"]))+"""</td>
        </tr>
        """

    #Prepare additional pieces of HTML code for eventual plastid analysis
    plastid_nav_html=""
    plastid_html=""
    if(plastid=="plastid"):
        plastid_nav_html = "<li><a href=\"#section2\">Plastid offset analysis</a></li>"
        plastid_html = """<span class="anchor" id="section2"></span>
        <h2 id="plastid">Plastid offset analysis</h2>
        <p>
        <table id="offset_table">
            <tr>
                <th id="table_header">RPF length</th>
                <th id="table_header">Offset</th>
            </tr>
            """+html_table+"""
        </table>
        <div class="img" id="plastid_img">
            <img src=\""""+offsets_img+"""\" alt="Plastid analysis" id="plastid_plot">
        </div>
        </p>
        """
    else:
        plastid_nav_html = "<li><a href=\"#section2\">Offsets overview</a></li>"
        plastid_html = """<span class="anchor" id="section2"></span>
                <h2 id="plastid">Offsets overview</h2>
                <p>
                <table id="offset_table">
                    <tr>
                        <th id="table_header">RPF length</th>
                        <th id="table_header">Offset</th>
                    </tr>
                    """ + html_table + """
                </table>
                </p>
                """

    #Structure of html file
    html_string = """<!DOCTYPE html>
<html>
<head>
   <title>Mapping QC Report """+run_name+"""</title>
   <meta charset="utf-8"></meta>
   <meta name="description" content="Overview HTML of all mappingQC results"></meta>
   <link href="https://fonts.googleapis.com/css?family=Indie+Flower" rel="stylesheet">
   <style>
        *{
            box-sizing: border-box;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }


        nav{
            float:left;
            padding: 15px;
            width: 17%;
            position: fixed;
            height: 100%;
            overflow: auto;
            border-right: ridge;
            border-color: lightgrey;
            margin-top: 60px;
            margin-left: -20px;
            padding-left: 20px;
            background-color: white;
            z-index:1;
        }

        nav ul {
            list-style-type: none;
            margin: 0px;
            padding: 5px;
            padding-top: 15px;

        }

        nav li{
            padding: 8px;
            margin-bottom: 8px;
            background-color: #33b5e5;
            color: #ffffff;
        }

        nav li:hover {
            background-color: #0099cc;
        }

        #content{
            position: absolute;
            margin-left:19%;
            height: 76%;
        }

        #rpf_phase{
            width:100%;
        }

        #header{
            background-color: grey;
            color: white;
            position:fixed;
            height: 2.7cm;
            width:110%;
            padding: 15px;
            padding-top: 10px;
            margin-left: -10px;
            margin-top: -30px;
            margin-right: -10px;
            margin-bottom: 10px;
            overflow: visible;
            z-index: 2;
        }

        #mappingqc{
            font-family: 'Indie Flower', cursive;
            font-size: 44px;
            padding-left: 10px;
            position: relative;
            z-index: 4;
        }
        #run_name{
            padding-left: 43px;
            position: relative;
            z-index: 4;
        }

        #biobix_logo{
            height:60%;
            position: absolute;
            right: 200px;
            top: 30px;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        .anchor{
            display: block;
            height: 14%; /*same height as header*/
            margin-top: -10px; /*same height as header*/
            visibility: hidden;
        }

        #analysis_info_table{
            border-style: none;
            border-width: 0px;
        }

        th {
            border-style: solid;
            border-width: 0px;
            border-color: white;
            border-collapse: collapse;
            padding: 5px;
            background-color: #33b5e5;
            color: #ffffff;
        }

        td {
            border-style: solid;
            border-width: 0px;
            border-color: white;
            border-collapse: collapse;
            background-color: #f2f2f2;
            padding: 5px;
        }

        img {
          max-width: 98%;
          height: auto;
          width: auto\9; /* ie8 */
        }

        #ranked_genes, #cumulative, #genes_density, #annotation_coding, #annotation_noncoding {
            width: 20cm;
        }

        #offset_table {
            float: left;
            display: block;
            margin-right: 120px;
        }

        #plastid_img {
            float: left;
            display: block;
            max-width: 600px;
        }

        #section3 {
            clear: left;
        }


        #footer{
            background-color: grey;
            color: white;
            position: fixed;
            bottom: 0cm;
            padding-left: 30px;
            margin-left: -30px;
            height: 0.7cm;
            width: 110%;
            z-index: 2;
        }
        #footer_content{
            position: fixed;
            bottom: -0.3cm;
        }
   </style>
</head>

<body>
    <div id="header">
        <h1><span id="mappingqc">Mapping QC</span><span id="run_name">"""+run_name+"""</span></h1>
        <img src=\"BIOBIX_logo.png\" alt="biobix_logo" id="biobix_logo">
    </div>

    <nav id="navigator">
        <ul>
            <li><a href="#section1">Analysis information</a></li>
            """+plastid_nav_html+"""
            <li><a href="#section3">Gene distributions</a></li>
            <li><a href="#section4">Metagenic classification</a></li>
            <li><a href="#section5">Total phase distribution</a></li>
            <li><a href="#section6">RPF phase distribution</a></li>
            <li><a href="#section7">Phase - relative position distribution</a></li>
            <li><a href="#section8">Triplet identity plots</a></li>
        </ul>
    </nav>

    <div id="content">
        <span class="anchor" id="section1"></span>
        <h2 id="info">Analysis information</h2>
        <p>
        <table id="analysis_info_table">
            <tr>
                <th id="table_header">Feature</th>
                <th id="table_header">Value</th>
            </tr>
            <tr>
                <td>Species</td>
                <td>"""+species+"""</td>
            </tr>
            <tr>
                <td>Input sam/bam file</td>
                <td>"""+samfile+"""</td>
            </tr>
            <tr>
                <td>Ensembl version</td>
                <td>"""+ensembl_version+"""</td>
            </tr>
            <tr>
                <td>Ensembl database</td>
                <td>"""+ens_db+"""</td>
            </tr>
            <tr>
                <td>Selected offset source</td>
                <td>"""+plastid+"""</td>
            </tr>
            <tr>
                <td>Used only unique alignments</td>
                <td>"""+unique+"""</td>
            </tr>
            <tr>
                <td>Total mapped genomic sequences</td>
                <td>"""+'{0:,}'.format(totmaps).replace(',',' ')+"""</td>
            </tr>
            <tr>
                <td>Analysis date</td>
                <td>"""+time.strftime("%A %d %b %Y")+"""</td>
            </tr>
            <tr>
                <td>Analysis time</td>
                <td>"""+time.strftime("%H:%M:%S")+"""</td>
            </tr>
        </table>
        </p>

        """+plastid_html+"""

        <span class="anchor" id="section3"></span>
        <h2 id="gene_distributions">Gene distributions</h2>
        <p>
            <div class="img">
            <img src=\"rankedgenes.png\" alt="Ranked genes" id="ranked_genes">
            </div>
        </p>
        <p>
            <div class="img">
            <img src=\"cumulative.png\" alt="Cumulative genes" id="cumulative">
            </div>
        </p>
        <p>
            <div class="img">
            <img src=\"density.png\" alt="Genes density" id="genes_density">
            </div>
        </p>

        <span class="anchor" id="section4"></span>
        <h2 id="metagenic_classification">Metagenic classification</h2>
        <p>
            <div class="img">
            <img src=\"annotation_coding.png\" alt="Metagenic classification coding" id="annotation_coding">
            </div>
        </p>
        <p>
            <div class="img">
            <img src=\"annotation_noncoding.png\" alt="Noncoding classification" id="annotation_noncoding">
            </div>
        </p>

        <span class="anchor" id="section5"></span>
        <h2 id="tot_phase">Total phase distribution</h2>
        <p>
            <div class="img">
            <img src=\"tot_phase.png" alt="total phase plot" id="tot_phase_img">
            </div>
        </p>

        <span class="anchor" id="section6"></span>
        <h2 id="phase_rpf_distr">RPF phase distribution</h2>
        <p>
            <div class="img">
            <img src=\"rpf_phase.png" alt="rpf phase plot" id="rpf_phase_img">
            </div>
        </p>

        <span class="anchor" id="section7"></span>
        <h2 id="phase_relpos_distr">Phase - relative position distribution</h2>
        <p>
            <div class="img">
            <img src=\"phase_relpos_distr.png" alt="phase relpos distr" id="phase_relpos_distr_img">
            </div>
        </p>

        <span class="anchor" id="section8"></span>
        <h2 id="triplet_identity">Triplet identity plots</h2>
        <p>
            <div class="img">
            <img src=\"triplet_id.png" alt="triplet identity plots" id="triplet_id_img">
            </div>
        </p>
        <br><br>
    </div>

    <div id="footer">
        <p id="footer_content">Generated with mQC - BioBix lab Ghent (Belgium) - Steven Verbruggen</p>
    </div>

</body>
</html>
    """

    #Generate html file
    html_file = open(outfile, 'w')
    html_file.write(html_string)
    html_file.close()

    return

## Plot triplet identity data
def triplet_plots(data, outputfolder):
    outfile = outputfolder+"/triplet_id.png"

    sns.set_palette('terrain') #Palette
    fig = plt.figure(figsize=(36, 32))
    grid = GridSpec(8, 9) #Construct grid for subplots
    grid_i = -1 #Grid coordinates
    grid_j = 0
    for triplet in sorted(data.keys(), key=get_AA):
        grid_i += 1
        if grid_i == 8:
            grid_i = 0
            grid_j += 1
        ax = plt.subplot(grid[grid_j,grid_i]) #Define subplot axes element in grid
        df = pd.DataFrame.from_dict(data[triplet], orient="index") #By index for right orientation
        df = df.sort_index(axis=0)
        labels_list = df[0].values.tolist()
        labels_list = map(format_thousands, labels_list)
        df.plot(kind="pie", subplots="True", autopct='%.1f%%', ax=ax, legend=None, labels=labels_list)
        #Individual legends off, subplots="True" for evading selecting y column error, autopercentage
        ax.set(ylabel='') #Do not plot y column label
        if triplet=="ATG":
            title_color=hex2color('#00ff00')
        elif triplet=="TGA" or triplet=="TAG" or triplet=="TAA":
            title_color=hex2color("#ff0000")
        else:
            title_color="k"
        ax.set_title(triplet+": "+get_AA(triplet), {'fontsize': 36}, color=title_color) #Put triplet in title
    handles, labels = ax.get_legend_handles_labels() #Get legend information of last ax object
    leg = fig.legend(handles, ["Phase 0", "Phase 1", "Phase 2"], bbox_to_anchor=(1, 0.53), fontsize=36)#Define legend
    leg.get_frame().set_edgecolor('b')
    plt.tight_layout() #Prevent overlapping elements
    fig.savefig(outfile)

    return

## Make plot of relative phase against RPF length
def phase_position_distr(tmpfolder, outfolder):

    #Input data, read in to pandas data frame
    inputdata_adress = tmpfolder+"/mappingqc/pos_table_all.csv"
    inputdata = pd.read_csv(inputdata_adress, sep=',', header=None, names=["phase", "rel_position"])

    #Split data based on phase
    data0 = inputdata[inputdata["phase"]==0]["rel_position"]
    data1 = inputdata[inputdata["phase"] == 1]["rel_position"]
    data2 = inputdata[inputdata["phase"] == 2]["rel_position"]

    #Define 20 bins
    bins = np.linspace(0,1,21)

    #Plot data
    fig, ax = plt.subplots(1, 1)
    ax.hist([data0,data1,data2], bins, label=["Phase 0", "Phase 1", "Phase 2"])
    ax.set_facecolor("#f2f2f2")
    lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    #Axis info
    plt.ylabel("Counts")
    plt.xlabel("Relative position in sequence")
    plt.xlim([0, 1])

    #Save output
    plt.tight_layout()
    fig.savefig(outfolder+"/phase_relpos_distr.png", bbox_extra_artists=(lgd,), bbox_inches='tight') #Make room for legend

    #Close matplotlib environment
    plt.close()

    return


## Make plot of RPF against phase as a grouped 2D bar chart
def plot_rpf_phase_grouped2D(phase_distr, outfile):

    #Parse data into Pandas data frame
    df = pd.DataFrame.from_dict(phase_distr, orient="index")
    df = df[['0','1','2']] #Reorder columns
    df = df.stack() #Put all phases as separated observations
    df = df.reset_index()
    df.columns = ['RPF length', 'Phase', 'Count']

    #Set figure
    sns.set_style(style="whitegrid")
    sns.set_palette("terrain")
    fig, ax = plt.subplots(1, 1)

    #Background color
    ax.set_facecolor("#f2f2f2")

    #Plot
    sns.factorplot(x='RPF length', y='Count', hue='Phase', data=df, ax=ax, kind="bar")
    sns.despine()

    #Y label
    ax.set_ylabel("Count")

    #Legend position
    ax.legend(title="Phase", loc='center right', bbox_to_anchor=(1.12, 0.5), ncol=1)

    #Finish plot
    plt.tight_layout()

    #Save figure
    fig.savefig(outfile)

    return


## Make plot of RPF against phase with mayavi
def plot_rpf_phase_mayavi(phase_distr, outfile):
    from mayavi import mlab

    # Parameters
    lensoffset = 0.5
    spread_factor = 2

    # Init data structures
    s = []
    x = [0, 1, 2]

    # Parse
    for rpf in sorted(phase_distr.keys()):
        data_row = []
        for phase in x:
            data_row.append(phase_distr[rpf][str(phase)])
        s.append(data_row)
    s = np.array(s)
    y = sorted(phase_distr.keys(), reverse=True)

    # Z data scaling parameters
    mean_s = np.mean(s)
    order_s = math.floor(math.log10(mean_s))
    max_s_axis = int(math.ceil(np.max(s) / (10 ** order_s)))

    # Bottom mesh
    xpos, ypos = np.meshgrid(x, y)

    # Figure
    mlab.figure(size=(400000, 320000), bgcolor=(1, 1, 1))

    # Colors
    # Color map
    cs = []
    for i in range(0, 220, int(220 / len(y)) + 1):
        clr = cm.terrain(i)
        cs.append(clr[0:3])  # Save as RGB, not RGBA

    # Bars
    s_plot = s / (10 ** order_s)
    for i in range(0, len(y)):
        RPF = ypos[i]
        phase = xpos[i]
        data_z = s_plot[i]
        color = cs[i]
        mlab.barchart(RPF * spread_factor, phase * spread_factor, data_z, color=color, line_width=10)

    # Axes
    yy = np.arange((min(x) - 0.25) * spread_factor, (max(x) + lensoffset) * spread_factor, 0.01)
    yx = np.repeat((max(y) + lensoffset) * spread_factor, len(yy))
    yz = np.repeat(0, len(yy))

    xx = np.arange((min(y) - 0.25) * spread_factor, (max(y) + lensoffset) * spread_factor, 0.01)
    xy = np.repeat((max(x) + lensoffset) * spread_factor, len(xx))
    xz = np.repeat(0, len(xx))

    z_ax_max = math.ceil(np.max(s) / (10 ** order_s))
    zz = np.arange(0, z_ax_max, 0.01)
    zx = np.repeat((min(y) - 0.25) * spread_factor, len(zz))
    zy = np.repeat((max(x) + lensoffset) * spread_factor, len(zz))

    mlab.plot3d(yx, yy, yz, line_width=0.01, tube_radius=0.01, color=(0, 0, 0))
    mlab.plot3d(zx, zy, zz, line_width=0.01, tube_radius=0.01, color=(0, 0, 0))
    mlab.plot3d(xx, xy, xz, line_width=0.01, tube_radius=0.01, color=(0, 0, 0))

    # Axes labels
    mlab.text3d((np.mean(y) + 1) * spread_factor, (max(x) + lensoffset + 1.5) * spread_factor, 0, 'RPF',
                color=(0, 0, 0), scale=0.6, orient_to_camera=False, orientation=[0, 0, 180])
    mlab.text3d((max(y) + lensoffset + 1.25) * spread_factor, (np.mean(x) - 1) * spread_factor, 0, 'Phase',
                color=(0, 0, 0), scale=0.6, orient_to_camera=False, orientation=[0, 0, 90])
    mlab.text3d((min(y) - 0.5) * spread_factor, (max(x) + 1.75) * spread_factor, np.max(s_plot - 4) / 2,
                'Counts (10^{0:g})'.format(order_s), color=(0, 0, 0), scale=0.6, orient_to_camera=False,
                orientation=[180, 90, 45])

    # Axes ticks
    # Phase
    for i in x:
        mlab.text3d((max(y) + lensoffset + 0.5) * spread_factor, i * spread_factor, 0, str(i), color=(0, 0, 0),
                    scale=0.5)
        xx_tick = np.arange((min(y) - 0.25) * spread_factor, (max(y) + lensoffset) * spread_factor + 0.2, 0.01)
        xy_tick = np.repeat(i * spread_factor, len(xx_tick))
        xz_tick = np.repeat(0, len(xx_tick))
        mlab.plot3d(xx_tick, xy_tick, xz_tick, line_width=0.01, tube_radius=0.01, color=(0.7, 0.7, 0.7))
    # RPF
    for j in range(0, len(y)):
        mlab.text3d((j + min(y) + 0.35) * spread_factor, (max(x) + lensoffset + 0.5) * spread_factor, 0, str(y[j]),
                    color=(0, 0, 0), scale=0.5)
        yy_tick = np.arange((min(x) - 0.25) * spread_factor, (max(x) + lensoffset) * spread_factor + 0.2, 0.01)
        yx_tick = np.repeat((j + min(y)) * spread_factor, len(yy_tick))
        yz_tick = np.repeat(0, len(yy_tick))
        mlab.plot3d(yx_tick, yy_tick, yz_tick, line_width=0.01, tube_radius=0.01, color=(0.7, 0.7, 0.7))
    # Counts
    for k in range(0, max_s_axis + 1, 2):
        mlab.text3d((min(y) - 0.5) * spread_factor, (max(x) + 0.75) * spread_factor, k, str(k), color=(0, 0, 0),
                    scale=0.5)
        xx_back = np.arange((min(y) - 0.25) * spread_factor, (max(y) + lensoffset) * spread_factor, 0.01)
        xy_back = np.repeat((min(x) - 0.25) * spread_factor, len(xx_back))
        xz_back = np.repeat(k, len(xx_back))
        mlab.plot3d(xx_back, xy_back, xz_back, line_width=0.01, tube_radius=0.01, color=(0.7, 0.7, 0.7))
        yy_side = np.arange((min(x) - 0.25) * spread_factor, (max(x) + lensoffset) * spread_factor, 0.01)
        yx_side = np.repeat((min(y) - 0.25) * spread_factor, len(yy_side))
        yz_side = np.repeat(k, len(yy_side))
        mlab.plot3d(yx_side, yy_side, yz_side, line_width=0.01, tube_radius=0.01, color=(0.7, 0.7, 0.7))

    # Side surfaces
    y_wall, z_wall = np.mgrid[(min(y) - 0.25) * spread_factor:(max(y) + lensoffset) * spread_factor:2j, 0:z_ax_max:2j]
    x_wall = np.zeros_like(y_wall) - lensoffset

    x_wall2, z_wall2 = np.mgrid[(min(x) - 0.25) * spread_factor:(max(x) + lensoffset) * spread_factor:2j, 0:z_ax_max:2j]
    y_wall2 = np.zeros_like(x_wall2) + ((min(y) - 0.25) * spread_factor)

    y_wall3, x_wall3 = np.mgrid[(min(y) - 0.25) * spread_factor:(max(y) + lensoffset) * spread_factor:2j,
                       (min(x) - 0.25) * spread_factor:(max(x) + lensoffset) * spread_factor:2j, ]
    z_wall3 = np.zeros_like(y_wall3)

    mlab.mesh(y_wall, x_wall, z_wall, color=(1, 1, 1))
    mlab.mesh(y_wall2, x_wall2, z_wall2, color=(1, 1, 1))
    mlab.mesh(y_wall3, x_wall3, z_wall3, color=(1, 1, 1))

    # Camera
    mlab.view(azimuth=55, elevation=65, distance='auto')

    # Export figure
    mlab.savefig(outfile)

    return


## Make plot of RPF against phase with MPL toolkits (pyplot)
def plot_rpf_phase_pyplot3D(phase_distr, outfile):
    from mpl_toolkits.mplot3d import Axes3D

    #Initialize fig and axes
    fig = plt.figure(figsize=(20,13))
    ax = fig.gca(projection='3d')
    axis_rate = 3 / float(len(phase_distr.keys()))
    ax.pbaspect = [axis_rate, 1, 0.5]  # Aspect ratio based on proportions of x and y axis
    '''
    If you want no square axis:
    edit the get_proj function inside site-packages\mpl_toolkits\mplot3d\axes3d.py (and remove .pyc file!):

    try:
        self.localPbAspect=self.pbaspect
        zoom_out = (self.localPbAspect[0]+self.localPbAspect[1]+self.localPbAspect[2])
    except AttributeError:
        self.localPbAspect=[1,1,1]
        zoom_out = 0
    xmin, xmax = self.get_xlim3d() /  self.localPbAspect[0]
    ymin, ymax = self.get_ylim3d() /  self.localPbAspect[1]
    zmin, zmax = self.get_zlim3d() /  self.localPbAspect[2]

    # transform to uniform world coordinates 0-1.0,0-1.0,0-1.0
    worldM = proj3d.world_transformation(xmin, xmax,
                                             ymin, ymax,
                                             zmin, zmax)

    # look into the middle of the new coordinates
    R = np.array([0.5*self.localPbAspect[0], 0.5*self.localPbAspect[1], 0.5*self.localPbAspect[2]])
    xp = R[0] + np.cos(razim) * np.cos(relev) * (self.dist+zoom_out)
    yp = R[1] + np.sin(razim) * np.cos(relev) * (self.dist+zoom_out)
    zp = R[2] + np.sin(relev) * (self.dist+zoom_out)
    E = np.array((xp, yp, zp))


    then add one line to this script to set pbaspect:

    ax = fig.gca(projection='3d')
    ax.pbaspect = [2.0, 0.6, 0.25] #e.g.
    '''

    #Make arrays for x- and y-coordinates
    x = np.asarray([0,1,2]).astype(np.float)
    y = np.asarray(sorted(phase_distr.keys())).astype(np.float)
    xmin = int(min(x))
    xmax = int(max(x))
    ymin= int(min(y))
    ymax = int(max(y))

    #Make a grid so that x- and y-coordinate for each point are given
    xpos, ypos = np.meshgrid(x[:] - 0.125, y[:] - 0.375)

    #Flatten: transform 2 dimensional array to 1 dimensional
    xpos = xpos.flatten('F')
    ypos = ypos.flatten('F')
    zpos = np.zeros_like(xpos)  # Make for z-coordinate an array of zeroes of the same length

    #Length of the bars
    dx = 0.5 * np.ones_like(xpos)
    dy = dx.copy()

    #Sort phase distr dict based on keys and save as z lengths
    keys_sorted_1 = sorted(phase_distr.keys())
    keys_sorted_2 = sorted(phase_distr[keys_sorted_1[0]].keys())
    dz = []

    for key2 in keys_sorted_2:
        for key1 in keys_sorted_1:
            dz.append(phase_distr[key1][key2])

    #Color map
    cs=[]
    for i in range(0,300,int(300/len(y))+1):
        clr = cm.terrain(i)
        cs.append(clr)

    #Plot
    bars = ax.bar3d(xpos, ypos, zpos, dx, dy, dz, zsort='max', alpha=0.99, color=cs*3)
    bars.set_edgecolor('k')

    #Axis ticks
    ticksxpos = np.arange(xmin, xmax+1, 1)
    ticksxlabs =range(xmin,xmax+1,1)
    plt.xticks(ticksxpos,ticksxlabs)
    ax.tick_params(axis='x', which='major', labelsize=20, pad=15)

    ticksypos = np.arange(ymin, ymax+1,1)
    ticksylabs=range(ymin,ymax+1,1)
    plt.yticks(ticksypos,ticksylabs)
    ax.tick_params(axis='y', which='major', labelsize=20, pad=15)

    ax.tick_params(axis='z', which='major', labelsize=20, pad=40)

    #Axis labels
    plt.xlabel('Phase', labelpad=60, fontsize=30)
    plt.ylabel('RPF length', labelpad=100, fontsize=30)
    ax.set_zlabel('counts', labelpad=90, fontsize=30)

    #Camera point angle
    ax.view_init(azim=-30)

    #Place axes in the middle of the fig environment
    ax.set_position([-0.35, -0.15, 1.5, 1.5])

    #Save as output
    fig.savefig(outfile)

    plt.close()

    return

## Make plot of total phase distribution
def plot_total_phase(distr, outfile):


    #Define figure and axes
    sns.set_style(style="whitegrid")
    sns.set_palette("terrain")
    fig, ax = plt.subplots(1, 1)

    #Parse data into arrays
    x = [0, 1, 2]
    y = [distr[k] for k in sorted(distr.keys())]

    #Set exponent base of y ticks
    majorFormatter = FixedOrderFormatter(6)
    ax.yaxis.set_major_formatter(majorFormatter)

    #Make plot
    sns.barplot(x, y, ax=ax)


    #Axis labels
    plt.xlabel('Phase')
    plt.ylabel('Counts')

    #Remove box lines around plot
    sns.despine()

    #Face color
    ax.set_facecolor("#f2f2f2")

    #Finish plot (not that much influence)
    plt.tight_layout()

    #Save output
    fig.savefig(outfile)

    return

class FixedOrderFormatter(ScalarFormatter):
    """Formats axis ticks using scientific notation with a constant order of
    magnitude"""
    def __init__(self, order_of_mag=0, useOffset=True, useMathText=False):
        self._order_of_mag = order_of_mag
        ScalarFormatter.__init__(self, useOffset=useOffset,
                                 useMathText=useMathText)
    def _set_orderOfMagnitude(self, range):
        """Over-riding this to avoid having orderOfMagnitude reset elsewhere"""
        self.orderOfMagnitude = self._order_of_mag

## Get plot data out of results DB
def get_plot_data(tmpfolder):

    #Init
    phase_distr = defaultdict(lambda: defaultdict())
    total = defaultdict()
    total['0'] = 0
    total['1'] = 0
    total['2'] = 0
    triplet_data = defaultdict(lambda: defaultdict())

    #RPF phase distribution
    phase_distr_tmp_file = tmpfolder+"/mappingqc/rpf_phase.csv"
    with open(phase_distr_tmp_file, "r") as RPD:
        for line in RPD:
            elements = line.split(',')
            phase_distr[elements[0]]['0'] = int(elements[1])
            phase_distr[elements[0]]['1'] = int(elements[2])
            phase_distr[elements[0]]['2'] = int(elements[3])

    #Total phase distribution
    for rpf in phase_distr.keys():
        #parse
        total['0'] = total['0'] + phase_distr[rpf]['0']
        total['1'] = total['1'] + phase_distr[rpf]['1']
        total['2'] = total['2'] + phase_distr[rpf]['2']

    #Triplet data
    triplet_tmp_file = tmpfolder+"/mappingqc/total_triplet.csv"
    with open(triplet_tmp_file, "r") as TripRead:
        for line in TripRead:
            elements = line.split(',')
            triplet_data[elements[0]][int(elements[1])] = int(elements[2])

    return phase_distr, total, triplet_data

## Get the number of primary (bit flag of 0x100)alignments out of samfile
def maps_out_of_sam(sam, galaxy, galaxysam, tmpfolder):

    #Init
    tot_maps = 0

    #Convert to sam if input was a bam file
    ext = sam.rsplit('.',1)[1]
    if ext=='bam':
        sam = tmpfolder+"/input.sam"
    elif galaxy=='Y' and galaxysam=='N':
        sam = tmpfolder+"/input.sam"

    #Use samtools and wc -l for this
    os.system("samtools view -S -F 0x100 "+sam+ " 2> /dev/null | wc -l > count.txt")
    #Read in result
    with open("count.txt", 'r') as IN:
        try:
            tot_maps = int(IN.readline())
        except:
            print "Error: could not parse total alignment count"

    #Remove in file
    os.system("rm -rf count.txt")

    return tot_maps

def format_thousands(x):
    return '{:,}'.format(int(x)).replace(",", " ")


def get_AA(item):

    codontable = get_codontable()
    AA = codontable[item]

    return AA


def get_codontable():

    codontable = {
        'ATA': 'Ile', 'ATC': 'Ile', 'ATT': 'Ile', 'ATG': 'Met',
        'ACA': 'Thr', 'ACC': 'Thr', 'ACG': 'Thr', 'ACT': 'Thr',
        'AAC': 'Asn', 'AAT': 'Asn', 'AAA': 'Lys', 'AAG': 'Lys',
        'AGC': 'Ser', 'AGT': 'Ser', 'AGA': 'Arg', 'AGG': 'Arg',
        'CTA': 'Leu', 'CTC': 'Leu', 'CTG': 'Leu', 'CTT': 'Leu',
        'CCA': 'Pro', 'CCC': 'Pro', 'CCG': 'Pro', 'CCT': 'Pro',
        'CAC': 'His', 'CAT': 'His', 'CAA': 'Gln', 'CAG': 'Gln',
        'CGA': 'Arg', 'CGC': 'Arg', 'CGG': 'Arg', 'CGT': 'Arg',
        'GTA': 'Val', 'GTC': 'Val', 'GTG': 'Val', 'GTT': 'Val',
        'GCA': 'Ala', 'GCC': 'Ala', 'GCG': 'Ala', 'GCT': 'Ala',
        'GAC': 'Asp', 'GAT': 'Asp', 'GAA': 'Glu', 'GAG': 'Glu',
        'GGA': 'Gly', 'GGC': 'Gly', 'GGG': 'Gly', 'GGT': 'Gly',
        'TCA': 'Ser', 'TCC': 'Ser', 'TCG': 'Ser', 'TCT': 'Ser',
        'TTC': 'Phe', 'TTT': 'Phe', 'TTA': 'Leu', 'TTG': 'Leu',
        'TAC': 'Tyr', 'TAT': 'Tyr', 'TAA': 'STOP', 'TAG': 'STOP',
        'TGC': 'Cys', 'TGT': 'Cys', 'TGA': 'STOP', 'TGG': 'Trp',
    }

    return codontable

## Data Dumper for recursively printing nested dictionaries and defaultDicts ##
def print_dict(dictionary, indent='', braces=0):
    """
    :param dictionary: dict or defaultdict to be printed
    :param indent: indentation
    :param braces:
    :return: void
    """

    for key, value in dictionary.iteritems():
        if isinstance(value, dict):
            print '%s%s%s%s' % (indent, braces * '[', key, braces * ']')
            print_dict(value, indent + '  ', braces)
        else:
            print indent + '%s = %s' % (key, value)



#######Set Main##################
if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        traceback.print_exc()
#################################