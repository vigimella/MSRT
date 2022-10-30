<h1 class="code-line" data-line-start=0 data-line-end=1 ><a id="CICD_Analysis__Masters_Degree_Project_0"></a>CI-CD Analysis - Master’s Degree Project</h1>
<p class="has-line-data" data-line-start="2" data-line-end="3">Once Dockerfile has started, the script can filter the repositories’ commits. Using PyDriller the tool clones the repo and starts the repository mining. Once finished the mining, all commits are saved in a CSV file. All CSV files are filtered using keywords stored in a list.</p>
<p class="has-line-data" data-line-start="4" data-line-end="5">Only the commits with the “.yml” file modified that contain a word in the previously cited list are saved in a Sqlite DB.</p>
<h2 class="code-line" data-line-start=6 data-line-end=7 ><a id="Docker_Execution_6"></a>Docker Execution</h2>
<pre><code class="has-line-data" data-line-start="9" data-line-end="12" class="language-sh"><span class="hljs-built_in">cd</span> ~/ci-cd-analysis
docker-compose up --build
</code></pre>
<h2 class="code-line" data-line-start=13 data-line-end=14 ><a id="Docker_Stop_13"></a>Docker Stop</h2>
<pre><code class="has-line-data" data-line-start="16" data-line-end="19" class="language-sh"><span class="hljs-built_in">cd</span> ~/ci-cd-analysis
docker-compose down -v
</code></pre>

