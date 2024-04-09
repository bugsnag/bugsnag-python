require "os"

def parameter_overrides(handler_name = nil)
  overrides = [
    "--parameter-overrides",
    # PYTHON_TEST_VERSION is defined in env.rb
    "ParameterKey=Runtime,ParameterValue=python#{PYTHON_TEST_VERSION}",
  ]

  overrides << "ParameterKey=Handler,ParameterValue=#{handler_name}" unless handler_name.nil?

  overrides.join(" ")
end

Given("I build the lambda function") do
  step(%Q{I run the service "aws-lambda" with the command "sam build BugsnagAwsLambdaTestFunction #{parameter_overrides}"})
end

Given("I invoke the lambda handler {string}") do |handle_name|
  command = [
    "sam local invoke BugsnagAwsLambdaTestFunction",
    "--container-host #{current_ip}",
    "--container-host-interface 0.0.0.0",
    "--docker-volume-basedir $PWD/features/fixtures/aws-lambda/app/.aws-sam/build",
    parameter_overrides(handle_name),
  ]

  step(%Q{I run the service "aws-lambda" with the command "#{command.join(" ")}"})
end

Given("I run the lambda function {string}") do |handler_name|
  steps(%Q{
    Given I build the lambda function
    And I invoke the lambda handler "#{handler_name}"
  })
end

Given("I run the lambda handler {string} with the {string} event") do |handler_name, event|
  steps(%Q{
    Given I build the lambda function
    And I invoke the lambda handler "#{handler_name} --event events/#{event}"
  })
end
