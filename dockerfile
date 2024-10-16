# 基础镜像，使用官方的 R 镜像
FROM r-base

# 安装R所需的系统依赖
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libmysqlclient-dev \
    libfontconfig1-dev \
    libpng-dev \
    libjpeg-dev

# 安装常用的R包，包括作图相关包
RUN R -e "install.packages(c('beginr', 'BIFIEsurvey', 'lessR', 'dslabs', 'ChaosGame', 'childesr', 'earnr', 'olsrr', 'rODE', 'repurrrsive', 'tidyxl', 'stevedore', 'RMySQL', 'pagedown', 'tmap', 'dataPreparation', 'htmlTable', 'OpenImageR', 'REKKL', 'smartdata', 'cdata', 'abstractr', 'shiny', 'kutils', 'pkgnet', 'rsparkling', 'geoknife', 'MazamaSpatialUtils', 'cleanerR', 'SQRL', 'crul', 'bitsqueezr', 'timeR', 'OpenCL', 'Ohmage', 'httr', 'httptest', 'pkgsearch', 'googleAnalyticsR', 'AzureContainers', 'AzureStor', 'AzureVM', 'spatialwidget', 'codetools', 'ggplot2', 'plotly', 'gridExtra', 'cowplot', 'RColorBrewer', 'scales', 'ggthemes', 'lattice', 'vcd', 'corrplot'), repos='http://cran.r-project.org')"

# 创建工作目录
WORKDIR /usr/src/app

# 将运行脚本拷贝到容器内
COPY run_r_script.sh /usr/src/app/

RUN chmod +x run_r_script.sh

# 定义启动命令
CMD ["./run_r_script.sh"]
