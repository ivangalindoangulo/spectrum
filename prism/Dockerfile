FROM continuumio/miniconda3

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy environment file
COPY environment.yml .

# Create environment (using name 'data_inv')
RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "data_inv", "/bin/bash", "-c"]

# Verify installation
RUN python --version

# IMPORTANT: The ENTRYPOINT ensures `conda run` executes the command
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "data_inv"]

# Default command
CMD ["python", "main.py"]  
