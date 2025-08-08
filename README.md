# Media Studio for Retail on GCP

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![Framework](https://img.shields.io/badge/Framework-Streamlit-red)
![Cloud](https://img.shields.io/badge/Cloud-Google_Cloud_Platform-blue)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A Streamlit application designed for Generative AI media creation in the retail sector, powered by Google Cloud Platform.

## 🌟 About The Project

Media Studio for Retail is an interactive web application that leverages the power of Google Cloud's generative AI models to create stunning and customized media assets for retail and e-commerce. Whether you need to generate new product images, create lifestyle shots, or produce marketing copy, this tool provides an intuitive interface to streamline your creative workflow.

This application is built to demonstrate the capabilities of Google's latest AI models for practical retail use cases.

### ✨ Features

* **Product Customization - Image Generation:** Use exisiting PDP/images of a product to generate new images.
* **Background Replacement:** Seamlessly replace the background of existing product photos.
* **Moodboard Creation:** Create professional moodboards with text and a click.
* **Virtual Try On:** Virtual Try On with Google Cloud's experimental model.
* **Multi-Page Interface:** Easy-to-navigate UI built with Streamlit.

## 🛠️ Technology Stack

This project is built with a modern, cloud-native stack:

* **Frontend:** [Streamlit](https://streamlit.io/)
* **Backend:** Python
* **Cloud Platform:** [Google Cloud Platform (GCP)](https://cloud.google.com/)
* **AI/ML:** [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai) (for generative models)

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

* **Python:** Version 3.12 or higher.
* **Google Cloud Account:** A GCP account with a project created.
* **Billing Enabled:** Billing must be enabled for your GCP project.
* **gcloud CLI:** The [Google Cloud CLI](https://cloud.google.com/sdk/gcloud) installed and authenticated.
* **APIs Enabled:** Make sure the `Vertex AI API` is enabled for your project. You can enable it by running:
    ```sh
    gcloud services enable aiplatform.googleapis.com --project YOUR_PROJECT_ID
    ```

### Installation

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/ssmostagh/media-studio-retail-gcp.git](https://github.com/ssmostagh/media-studio-retail-gcp.git)
    cd media-studio-retail-gcp
    ```

2.  **Create a virtual environment (recommended):**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```
    *On Windows, use `venv\Scripts\activate`*

3.  **Install the dependencies:**
    *(Note: A `requirements.txt` file is assumed. If you don't have one, you can create it with `pip freeze > requirements.txt` after installing the necessary packages.)*
    ```sh
    pip install -r requirements.txt
    ```
    Likely dependencies include `streamlit`, `google-cloud-aiplatform`, and `Pillow`.

4.  **Authenticate with Google Cloud:**
    If you have the `gcloud` CLI installed, the application should automatically pick up your credentials. Alternatively, you can set up Application Default Credentials:
    ```sh
    gcloud auth application-default login
    ```

## 🏃‍♀️ Usage

Once the installation is complete, you can run the Streamlit application with a single command:

```sh
streamlit run home.py
```

This will start the web server and open the application in your default web browser.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
