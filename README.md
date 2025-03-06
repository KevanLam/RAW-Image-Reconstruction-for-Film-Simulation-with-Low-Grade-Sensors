<a name="readme-top"></a>

# RAW Image Reconstruction for Film Simulation with Low-Grade Sensors 

## Authors
   - [Zhuoqian Yang](https://github.com/yzhq97)
   - [Kevan Lam Hopyang](https://github.com/KevanLam)


<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#authors">Authors</a></li>
        <li><a href="#project-description">Introduction</a></li>
      </ul>
    </li>
  </ol>
</details>



## Introduction
Film photography’s distinctive “look” is partly due to its ability to record and compress light information of high dynamic range, especially in the highlights, without clipping [1]. By preserving subtle gradations in highlight and shadow areas and compressing, film naturally reveals rich color nuances, which is a key contributor to its signature aesthetic.

<img src="https://github.com/user-attachments/assets/816dbf8d-09fc-4dca-a481-e56ea3e2c055" width="49%" style="display:inline-block"/> 
<img src="https://github.com/user-attachments/assets/d04c4f3d-5969-4bb5-b17e-2b76190552fe" width="49%" style="display:inline-block"/>


Digital film emulation has become increasingly popular, but most applications (e.g., Dazz, Dehancer, VSCO) assume availability of high-quality captures, while working off of images captured by relatively limited consumer camera sensors. These images tend to have a low dynamic range and lose highlight and shadow detail that film retains, making it impossible for current emulators to reproduce nuanced tones via compression.

This project aims to explore an approach that *recovers or generates a high dynamic range RAW-equivalent image from the limited RGB input*. By doing so, we can feed a simulated sensor output with higher bit-depth and more accurate color response into the film simulation pipeline, ensuring that the final result retains the highlight compression and color nuances that define the “film look.”
