# Use Anaconda base image
FROM continuumio/miniconda3:latest

# Set working directory
WORKDIR /app

# Copy environment file
COPY env.yaml .

# Create conda environment from env.yaml
RUN conda env create -f env.yaml

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "aalto_defence_hackathon_server_env", "/bin/bash", "-c"]

# Copy application code
COPY . .

# Create instance directory for SQLite database
RUN mkdir -p instance

# Expose port
EXPOSE 5000

# Activate the environment and run the application
CMD ["conda", "run", "--no-capture-output", "-n", "aalto_defence_hackathon_server_env", "python", "app.py"]
