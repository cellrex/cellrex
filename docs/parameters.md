# CellRex Parameters

-----
# Upload

## **Upload**
### Definition
Selection of the file to be uploaded.
### Usage Guidelines
After uploading a file, the initial selection of a new file will not be adopted.
### Attributes
- Datatype: Enumeration, String, File
- Range: One of the files in the specified Upload Folder
- Optional: No
### Dependencies
- Configuration pointing to a file location
- List of assets in the file location

# Subject

## **Species**
### Definition
The specific biological species from which the research sample is derived, providing fundamental taxonomic classification.
### Examples
- Human
- Mouse
- Rat
- ....
### Attributes
- Datatype: Enumeration, String
- Range: One of predefined from list in configuration
- Optional: No
### Dependencies
- Configuration

## **Origin**
### Definition
Defines the specific cellular source or type of biological material used in the experiment.
### Examples
- **Primary**: Primary cells are cells taken directly from living tissue (e.g. animals) and established for growth in vitro.
- **iPSC**: Induced pluripotent stem cells are derived from skin or blood cells that have been reprogrammed back into an embryonic-like pluripotent state that enables the development of an unlimited source of any type of human cell needed for therapeutic purposes.
- **eSC**: Embryonic stem cells are pluripotent cells with the ability to differentiate into any mature cell types of the trilaminar germ lines. They are taken from early-stage embryos — a group of cells that forms when eggs are fertilized with sperm at an in vitro fertilization clinic.
### Attributes
- Datatype: Enumeration, String
- Range: One of Primary, iPSC, eSC
- Optional: No
### Dependencies
- Configuration

## **Organ Type**
### Definition
The specific organ classification, providing context for the biological system in the biological material used in the experiment.
### Usage Guidelines
Organ Type has downward dependencies on the cell type where a selection of an organ type implies the available cell types.
### Examples
- Cardio
- Neuro
- Kidney
### Attributes
- Datatype: Enumeration, String
- Range: One of predefined from list in configuration
- Optional: No
### Dependencies
- Descendant: Cell Type

## **Cell Type**
### Definition
The specific cellular classification corresponding to the selected organ type, providing detailed characterization of the biological material.
### Usage Guidelines
- Cell Type has upward dependencies on the organ type
- Some cell types can be configured to be multi-cell types where a selection makes the selection of e.g. `brain regions` possible
### Attributes
- Datatype: String
- Range: Dependent on selected origin
- Optional: No
### Dependencies
- Ancestor: Organ Type
- Descendant: Brain Region

## **Brain Region**
### Definition
The specific cellular classification corresponding to a specific anatomical or functional area within the brain, which can be obtained through direct sampling or differentiation of stem/progenitor cells.
### Usage Guidelines
Brain Region has upward dependencies on the organ type, respectively Cell Type.
### Attributes
- Datatype: List of strings
- Range: predefined list in configuration
- Optional: Yes
### Dependencies
- Ancestor: Organ Type
- Ancestor: Cell Type (respectively MULTI_CELL_TYPES)

## **Protocol Name**
### Definition
A comprehensive documentation of the procedural steps used in creating and preparing the biological recording or experiment.
### Usage Guidelines
- Select the most accurate and detailed protocol from available options
- Minor changes to the selected protocol should be described in the referencing `notes`
- Protocols are loaded from the `protocols folder` specified in the configuration
- Further protocols can be added to the folder
- Further explanation on protocol loading:
	- TBD!
### Attributes
- Datatype: Text document, String, 
- Range: Protocols from the predefined 'protocols folder'
- Optional: No
### Dependencies
- Configuration pointing to respective file locations

## **Cell ID**
### Definition
A unique identifier located on the vial of purchased cells, especially primary cells.
### Usage Guidelines
- Enter the Cell ID if known to ensure accurate tracking of cell origin
- Can be given by the manufacturer or a custom ID given by the lab
- Leave blank if unknown, as this field is optional
### Attributes
- Datatype: String
- Range: Any alphanumeric string
- Optional: Yes
### Dependencies
- None

# Session

## Keywords
### Definition
Three to four descriptive terms summarizing the experiment's essence.
### Usage Guidelines
- Select keywords carefully to facilitate easier search and comprehension
- It is helpful that each file in the experiment contains the same keywords, otherwise the user should take care to select the corresponding `Experiment name`, and not the default generated one
### Attributes
- Datatype: List of strings
- Range: 1–5 keywords of predefined list in configuration
- Optional: No
### Dependencies
- Configuration defining a sorted list

## Experimenter
### Definition
The individual who generated the data.
### Usage Guidelines
- Enter the name of the person responsible for the experiment, rather than the person who is uploading the file in CellRex
### Examples
- John Doe as JDoe
- Jane Doe as JDoe2
### Attributes
- Datatype: String
- Range: Short name without blanks from predefined list in configuration
- Optional: No
### Dependencies
- Configuration defining a sorted list

## Lab
### Definition
The laboratory where the data were generated.
### Attributes
- Datatype: String
- Range: Any alphanumeric string from predefined list in configuration
- Optional: No
### Dependencies
- Configuration defining a sorted list

## Date of Measurement
### Definition
The date when the file to be uploaded was generated.
### Usage Guidelines
- Verify the accuracy of the date for proper organization.
- The date of measurement will be used to automatically generate the `experiment name`
- If the date of the current measurement file differs from the date of the first measurement file of the corresponding experiment, the correct experiment name must be selected.
### Attributes
- Datatype: Date
- Range: Valid dates in "YYYY-MM-DD" format in the range 01.01.2000-today
- Optional: No
### Dependencies
- None

## Time of Measurement
### Definition
The time when the measurement was started.
### Usage Guidelines
- Use the format "HH:MM."
- Enter if known, as this field is optional.
### Attributes
- Datatype: Time
- Range: Valid times in "HH:MM" format
- Optional: Yes
### Dependencies
- None

## Experiment Name
### Definition
An automatically generated name based on experiment details such as the date, experimenter, and keywords. The experiment name consists of the letters “exp”, the date of the first measurement file, the experimenter(s), and the first three keywords.
### Usage Guidelines
- Select the correct experiment name when dates, keywords and/or experimenter names differ across files.
- CellRex allows for the creation of a new experiment with the current date for each measurement file.
### Examples
- "exp_2024-12-03_ASmith_Neurospheres."
### Attributes
- Datatype: String
- Range: Alphanumeric string with defined structure, custom string not allowed
- Optional: No
### Dependencies
- Assets in the folder path generated from above entered information

## Precursor Experiment
### Definition
Links to previous experiments influencing the current one.
### Usage Guidelines
- Include all relevant precursor experiments to track cell history.
- Use this field to provide context for experimental conditions.
### Examples
A precursor experiment might assess the effect of a drug on cells that have survived, remain healthy, and are too valuable to discard. A subsequent experiment will then be performed on the same cells, which will be the current experiment.
### Attributes
- Datatype: List of strings
- Range: List of valid experiment names matching the current experiment
- Optional: Yes
### Dependencies
- Assets in the folder path generated from above entered information

## Sample ID
### Definition
A sample ID assigned to each sample to ensure accurate tracking and analysis throughout the experimental process
### Usage Guidelines
- Assign consecutive integer values to samples for consistency
- Ensure the Sample ID matches across associated data files
### Attributes
- Datatype: Integer
- Range: Positive integers
- Optional: No
### Dependencies
- None

## Age (DIV/DAP)

### Definition
The age of the culture at the time of analysis, measured in either **days in vitro (DIV)** or **days after plating (DAP)**.
### Further Information
- **DIV**: Following the thawing of cells, the number of days is counted continuously and labeled as ‘days in vitro’ (DIV). DIV 0 is equivalent to the day of thawing. In the event that the cells are plated directly on the substrate for analysis (MEA, coverslip, etc.), the age of the cell culture can be counted in DIV throughout the entirety of the experiment.

- **DAP**: When cells are first cultured on a specific substrate and later transferred to another, ‘days after plating’ is used to account for the age of the culture on the new substrate.
### Usage Guidelines
- If both are provided, DAP is used for folder creation.
### Examples
- **DIV**: A vial of rat neurons is thawed and the cells are plated directly on MEA chips. The analysis was conducted 10 days following the thawing process. In this instance, the age of the culture is 10 days in vitro (DIV).
- **DAP**: Neurospheres were cultured for 30 days in low-adhesion plates and then transferred to a MEA chip. The analysis was conducted after a period of 14 days during which the neurospheres were cultured on MEAs. In this instance, the age of the culture can be defined as follows: The culture was maintained for 30 days and 14 days after plating.
### Attributes
- Datatype: Integer
- Range: Positive integers
- Optional: No, one of the two must be supplied
### Dependencies
- None

## Number of Influence Groups
### Definition
Multiple influence groups are designated only for multiwell plates. Each group represents a unique grouping of influences on different wells. Influence groups allows easy referencing of influence locations to their respective control and sham locations.
### Usage Guidelines
- Even if no influence is examined in the experiment, select the influence “Control” for your data
- Influence groups can be utilized for the classification of multiple influences that affect the same cells concurrently. For example, influence group IG1 encompasses both treatment and disease, while IG2 refers exclusively to the disease.
### Examples
- A Multiwell Plate with 24 samples. 8 of them were controls, 8 were shams and 8 were treated with 10 µM LSD for 24 h
	- IG1 (Control, Sham, Pharmacology)
- A Multiwell Plate with 24 samples. 3 different LSD concentrations, the corresponding shams and control samples at the same time.
	- IG1 (Control, Sham, LSD concentration 1)
	- IG2 (Control, Sham, LSD concentration 2)
	- IG3 (Control, Sham, LSD concentration 3)
- A Multiwell Plate with 24 samples. All samples were hIPSC (from an Alzheimer patient) derived neurons. 12 of them were additionally irradiated with 15 Gy X-rays.
	- IG1 (Disease)
	- IG2 (Disease, Radiation)
### Attributes
- Datatype: Integer 
- Range: 1-5
- Optional: No
### Dependencies
- Source Code

## Influences
### Definition
Describes specific treatments or conditions, such as pharmacological agents or radiation, that are applied to cells for the purpose of studying their effects on cellular behavior, function, and responses.
### Further Information
#### **Control**: 
- **Definition**: The term ‘control’ is regarded as a form of influence, serving to establish a baseline condition against which experimental groups are evaluated. The control measurement can be used as a point of reference for subsequent influence or treatment.
- **Usage Guideline**: Even if no influence is examined in the experiment, select the influence `Control` for your data.
#### **Sham**:
- **Definition**: A 'sham' group represents a specific type of control group that undergoes a procedure or treatment that mimics the experimental conditions but does not involve the actual influence being tested. This distinction is important: while both control and sham groups serve as references, the sham group is designed to account for any effects that may arise from the experimental procedure itself, ensuring that the observed outcomes can be attributed solely to the actual influence.
- **Usage Guideline**: If no specific sham is available, use control as reference.
#### **Pharmacology**:
- **Definition**: A drug, along with its concentration, concentration unit, exposure time, and exposure time unit, is specified. The exposure time is the time period during which the cells were exposed to the drug.
- **Usage Guideline**: The available units are as follows: s - seconds, m - minutes, h - hours, d - days, inf – permanent.
#### **Radiation**:
- **Definition**: A radiation type is specified along with the dosage, dosage unit, exposure time, and exposure time unit. The exposure time is the time period during which the cells were exposed to the radiation.
- **Usage Guideline**: The available units are as follows: s - seconds, m - minutes, h - hours, d - days, inf – permanent.
#### Stimulus (Electrical stimulation):
- Not implemented yet
#### **Disease**:
- **Definition**: The term ‘disease’ is used to describe cells that are affected by a pathological condition.
### Usage Guidelines
- Select one or more influences relevant to the experiment.
- Always select "Control" if no specific influence is applied.
- Define sham groups for procedural controls.
- For a single well setup, the appropriate option is ‘SingleWell’. In a multiwell setup, it is possible to specify whether the influence is to be applied to the entire setup as ‘AllWell’ or to specific wells.
### Examples
- **Pharmacology**: "Drug A, 5 μM, 24 h."
- **Radiation**: "X-ray, 50 Gy, 10 min."
- **Sham**: "No radiation applied, mimic setup."
### Attributes
- Datatype: List of structured objects
- Range: /
- Optional: No
### Dependencies
- Source Code
- Configuration defining drop-down fields and selectors per influence

## Device
### Definition
The equipment used for data measurement.
### Further information
#### MEA
In the case of the Multi/Micro Electrode Array (MEA), the designation of the ‘lab device’ serves to identify the specific recording system and associated ‘chip type’. The term ‘chip ID’ is employed for the purpose of tracking a specific chip. Furthermore, the recording duration in seconds and the sample rate in Hz are included.
#### Microscope
A specific microscope along with a designated ‘magnification’ value. Additionally, a task is selected from the following options: ‘Brightfield’, ‘Ca2+ Imaging’, or ‘IF-Staining’. For Ca2+ Imaging, a calcium imaging dye is specified to visualize calcium ion concentrations in the cells. In the case of IF-Staining (Immunofluorescence Staining), available primary and secondary antibodies can be chosen. Furthermore, options for ‘conjugated antibodies’ (antibodies linked to a fluorescent dye) and ‘other dyes’ are also available for various staining applications.
### Attributes
- Datatype: Structured object
- Range: /
- Optional: No
### Dependencies
- Source Code
- Configuration defining drop-down fields and selectors per device

# General

## Raw Data Reviewed
### Definition
Indicates whether the raw data has been reviewed for quality and validity.
### Usage Guidelines
- Select “Yes” once the data has been assessed, a rating for the data can be cast to rank data by its quality
- Use this as a checkpoint before proceeding with further analysis.
### Attributes
- Datatype: Boolean
- Range: Yes/No
- Optional: No
### Dependencies
- None

## Notes
### Definition
Additional remarks or observations about the experiment, sample, or file that do not fit into other categories.
### Usage Guidelines
- Use for contextual information, clarifications, or unusual findings.
- Keep notes concise and relevant.
### Examples
- "Sample showed abnormal calcium signaling patterns."
- "Data recorded during power fluctuation, minor noise present."
### Attributes
- Datatype: String
- Range: Free text
- Optional: Yes
### Dependencies
- None