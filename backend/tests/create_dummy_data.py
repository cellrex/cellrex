import os
import random
from datetime import datetime, timedelta


def generate_dummy_upload_files(output_folder="share/upload", num_files=30):
    """
    Generate a set of files with diverse formats, names, and interconnected content.

    Args:
        output_folder (str): Path to the folder where files will be saved
        num_files (int): Number of files to generate
    """
    TOTAL_FILES = 0
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Extended lists for more variety
    file_extensions = [".dat", ".txt", ".csv", ".xml"]

    research_domains = [
        "Neuroscience",
        "Immunology",
        "Pharmacology",
        "Bioengineering",
        "Genetics",
        "Microbiology",
        "Molecular Biology",
        "Cellular Biology",
        "Tissue Engineering",
        "Computational Biology",
        "Systems Biology",
        "Synthetic Biology",
        "Biophysics",
        "Structural Biology",
        "Chemical Biology",
        "Bioinformatics",
        "Genomics",
        "Epigenetics",
        "Proteomics",
        "Metabolomics",
        "Translational Research",
        "Regenerative Medicine",
        "Stem Cell Biology",
        "Cancer Biology",
        "Oncology",
        "Hematology",
        "Infectious Diseases",
        "Neurology",
        "Psychiatry",
        "Behavioral Science",
        "Epidemiology",
        "Public Health",
        "Global Health",
        "Environmental Science",
        "Ecological Research",
        "Conservation Biology",
        "Marine Biology",
        "Agricultural Science",
        "Food Science",
        "Nutrition",
        "Medical Microbiology",
        "Medical Genetics",
        "Clinical Trials",
        "Pharmacogenomics",
        "Toxicology",
        "Environmental Toxicology",
        "Synthetic Organic Chemistry",
        "Medicinal Chemistry",
        "Bioanalytical Chemistry",
        "Analytical Chemistry",
        "Computational Chemistry",
        "Theoretical Chemistry",
        "Materials Science",
        "Nanotechnology",
        "Biomaterials",
        "Tissue Engineering",
        "Regenerative Medicine",
        "Biomechanics",
        "Mechanical Engineering",
        "Electrical Engineering",
        "Computer Science",
        "Data Science",
        "Artificial Intelligence",
        "Machine Learning",
        "Network Science",
        "Systems Engineering",
        "Robotics",
        "Autonomous Systems",
        "Cybernetics",
        "Computational Neuroscience",
        "Neural Engineering",
        "Brain-Computer Interfaces",
        "Cognitive Science",
        "Neuropsychology",
        "Behavioral Neuroscience",
        "Molecular Neurobiology",
        "Cellular Neurophysiology",
    ]

    experiment_stages = [
        "Preliminary Setup",
        "Research Proposal Development",
        "Literature Review",
        "Experimental Design",
        "Instrumentation and Equipment Preparation",
        "Data Collection",
        "Raw Data Processing",
        "Intermediate Analysis",
        "Model Development",
        "Hypothesis Testing",
        "Statistical Analysis",
        "Result Interpretation",
        "Conclusion Drawing",
        "Final Reporting",
        "Peer Review",
        "Revision and Editing",
        "Proofreading and Formatting",
        "Submission to Journal or Conference",
        "Review and Revision Based on Feedback",
        "Publication or Presentation",
    ]

    # Content generation helpers
    def generate_content(domain, stage, day=None, related_files=None):
        base_content = f"# {domain} Research - {stage}\n"
        if day:
            base_content += f"## Day {day} Report\n"

        if related_files:
            base_content += "### Related Files:\n"
            for file in related_files:
                base_content += f"- {file}\n"

        content_sections = [
            f"\n### Objective\nInvestigate key mechanisms in {domain} research.\n",
            f"\n### Methodology\n1. Implement {domain.lower()} protocol\n2. Collect and analyze data\n3. Document findings\n",
            f"\n### Key Observations\n- Significant finding in {domain} domain\n- Preliminary data trends observed\n",
            f"\n### Potential Implications\nFurther research needed in {domain} field.\n",
        ]

        return base_content + "".join(
            random.sample(content_sections, len(content_sections))
        )

    # Generated files tracker
    generated_files = []

    # Random seed for reproducibility
    random.seed(datetime.now().timestamp())

    # Create interconnected file sets
    for series_type in [
        "multi-day-study",
        "experiment-series",
        "research-progression",
        "field-research",
        "preliminary-study",
        "long-term-study",
        "short-term-trial",
        "pilot-project",
        "feasibility-study",
        "case-control-study",
        "cross-sectional-study",
        "retrospective-cohort-study",
        "prospective-cohort-study",
        "randomized-controlled-trial",
        "non-randomized-controlled-trial",
        "observational-study",
        "qualitative-study",
        "quantitative-study",
        "mixed-methods-study",
        "systematic-review",
        "meta-analysis",
        "review-of-literature",
        "protocol-study",
        "exploratory-study",
        "validation-study",
        "verification-study",
        "comparative-study",
        "incremental-study",
        "continuing-study",
    ]:
        # Select a domain for this series
        domain = random.choice(research_domains)
        base_timestamp = datetime.now() - timedelta(days=random.randint(0, 30))

        # Create a series of interconnected files
        series_files = []
        for i in range(random.randint(5, 10)):
            TOTAL_FILES += 1
            if TOTAL_FILES > num_files:
                return
            # Determine file extension
            ext = random.choice(file_extensions)

            # Create filename with series context
            stage = random.choice(experiment_stages)
            timestamp = (base_timestamp + timedelta(days=i)).strftime("%Y%m%d")
            filename = f"{series_type.replace('-', '_')}_{domain.lower().replace(' ', '_')}_{stage.lower().replace(' ', '_')}_{timestamp}_{i+1}{ext}"
            filepath = os.path.join(output_folder, filename)

            # Track files in this series
            series_files.append(filename)

            # Content generation with cross-referencing
            content = generate_content(
                domain,
                stage,
                day=i + 1,
                related_files=series_files[:-1] if len(series_files) > 1 else None,
            )

            # Write the file
            with open(filepath, "w") as f:
                f.write(content)

            generated_files.append(filename)
            print(f"Generated: {filename}")

    # Add some random additional files to reach total
    while TOTAL_FILES < num_files:
        domain = random.choice(research_domains)
        ext = random.choice(file_extensions)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"misc_{domain.lower().replace(' ', '_')}_{timestamp}{ext}"
        filepath = os.path.join(output_folder, filename)

        content = generate_content(domain, "Miscellaneous Research")

        with open(filepath, "w") as f:
            f.write(content)

        generated_files.append(filename)
        TOTAL_FILES += 1
        print(f"Generated: {filename}")

    return generated_files


# Example usage
if __name__ == "__main__":
    files = generate_dummy_upload_files()
    print(f"\nGenerated {len(files)} files in 'generated_files' directory.")
