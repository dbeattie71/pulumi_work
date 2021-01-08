import { Input, Output } from "@pulumi/pulumi"
import * as pulumi from "@pulumi/pulumi";
import * as fs from 'fs'

export interface OutputFileArgs {
  propName: string;
  prop: pulumi.Output<string>;
}

// Creates Datadog monitors and a dashboard for all the instances in the stack.
export class OutputFile extends pulumi.ComponentResource {
  public readonly outputFileName: string;

  constructor(name: string, args: OutputFileArgs, opts?: pulumi.ComponentResourceOptions) {

    super("custom:x:OutputFile", name, args, opts)

    const outputFileName = `${args.propName}.txt`

    writeEnvProp(outputFileName, args.propName, args.prop)

    this.outputFileName = outputFileName
  }
}

/////// helper function //////
function writeEnvProp(fileName: string, propName: string, prop: pulumi.Output<string>) {
  prop.apply(prop => {
    const outString = `${propName}=${prop}`

    fs.writeFile(fileName, outString, (err) => {
        // throws an error, you could also catch it here
        if (err) throw err;
        // success case, the file was saved
        console.log(`${outString} saved!`);
    });
  })

}

