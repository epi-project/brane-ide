import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin,
} from '@jupyterlab/application';


const plugin: JupyterFrontEndPlugin<void> = {
    id: 'brane_logger:plugin',
    autoStart: true,
    activate: (app: JupyterFrontEnd) => {
        // Register the mime type
        app.

        console.log('JupyterLab extension brane_logger is activated!');
    },
};

export default plugin;
