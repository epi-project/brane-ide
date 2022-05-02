import { JSONObject } from '@lumino/coreutils';
import * as ReactDOM from 'react-dom';
import * as React from 'react';
// import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
// import BarLoader from "react-spinners/BarLoader";

type Props = {
    inProgress: boolean;
    stdout: string;
    stderr: string;
    debug: string;
}

class Renderer {
    private _invocation: any;
    private _container: HTMLElement;

    constructor(invocation: JSONObject, container: HTMLElement, callback: Function) {
        this._invocation = invocation;
        this._container = container;

        this._render(callback);
    }

    /**
     *
     * @param invocation
     * @param callback
     */
    update(invocation: JSONObject, callback: Function) {
        // console.log("ReactApp: update()");

        if (invocation.status != this._invocation.status) {
            this._invocation = invocation;
            this._render(callback);
        }
    }

    /**
     *
     * @param invocation
     */
    deriveProps(invocation: JSONObject): Props {
        const inProgress = !(invocation["done"] as boolean);
        const stdout = invocation["stdout"] as string;
        const stderr = invocation["stderr"] as string;
        const debug = invocation["debug"] as string;

        return {
            inProgress,
            stdout,
            stderr,
            debug,
        };
    }

    /**
     *
     * @param callback
     */
    _render(callback: Function) {
        // console.log("ReactApp: _render()");
        const { inProgress, stdout, stderr, debug } = this.deriveProps(this._invocation);

        ReactDOM.render(
            <App inProgress={inProgress} stdout={stdout} stderr={stderr} debug={debug} />,
            this._container,
            () => callback(),
        );
    }
}

class App extends React.Component<Props> {
    /**
     *
     */
    render() {
        // console.log("App: render()");

        // If any debug messages, log to console
        if (this.props.debug.length > 0) { console.debug("Remote: " + this.props.debug); }

        // Otherwise, if not done, show the status indicator
        let to_write: JSX.Element[] = [];
        // if (this.props.inProgress) {
        //     to_write.push(
        //         <div className="invocation-renderer__output">
        //             <BarLoader color="#000" css="display: block" width={54} height={4} />
        //         </div>
        //     );
        // }

        // Otherwise, if any stdout, write it
        if (this.props.stdout.length > 0) {
            to_write.push(
                <div className="jp-RenderedText" data-mime-type="application/vnd.jupyter.stdout">
                    <pre>{this.props.stdout}</pre>
                </div>
            );
        }

        // Finally, if any stderr, write it
        if (this.props.stderr.length > 0) {
            to_write.push(
                <div className="jp-RenderedText" data-mime-type="application/vnd.jupyter.stderr">
                    <pre>{this.props.stderr}</pre>
                </div>
            );
        }

        // If there is anything to render, choose the appropriate wrapper type
        if (to_write.length == 1) {
            return to_write[0];
        } else if (to_write.length == 2) {
            return <div>
                {to_write[0]}
                {to_write[1]}
            </div>;
        } else if (to_write.length == 3) {
            return <div>
                {to_write[0]}
                {to_write[1]}
                {to_write[2]}
            </div>;
        }

        // Return nothing
        return [];
    }
}

export default Renderer;
